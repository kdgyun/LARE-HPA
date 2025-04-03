import multiprocessing
import math
from datetime import datetime
import os
import numpy as np
from api.online_arima import OnlineARIMA
from api.autoscaling import get_cpu_utilization, set_replicas, get_replicas
from controllers.scheduler import Scheduler
from api.metrics import get_prometheus_data
from api.threshold_coordinator import get_new_threshold
from api.hpa_stabilization_window_coordinator import get_new_stabilization_window_period
import logging


log_dir = os.path.join(os.path.dirname(__file__), '..', 'log')
os.makedirs(log_dir, exist_ok=True)


class HorizontalPodAutoscalerController:
    
    def __init__(self, namespace, deployment_name, app_name, container_name, target_cpu_utilization, min_replicas, max_replicas, metrics_period):
        self.namespace = namespace
        self.deployment_name = deployment_name
        self.app_name = app_name
        self.container_name = container_name
        self.target_cpu_utilization = multiprocessing.Value('d', target_cpu_utilization)
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.metrics_period = metrics_period
        self.model = None
        self.start_time = None
        self.is_active = False
        self.current_CDT_counter = multiprocessing.Value('i', 0)
        self.desired_CDT_counter = multiprocessing.Value('i', 1)
        self.min_CDT_counter = 1
        self.max_CDT_counter = 60
        self.general_logger = None
        self.error_logger = None
        self.autoscaler_logger = None
        self.threshold_logger = None
        self.CDT_logger = None

    def scale(self):
        if self.model is None:
            self.init_model()
        if self.general_logger is None or self.error_logger is None or self.autoscaler_logger is None or self.threshold_logger is None or self.CDT_logger is None:
            self.log_init()
            if self.general_logger is not None and self.error_logger is not None and self.autoscaler_logger is not None and self.threshold_logger is not None and self.CDT_logger is not None:
                self.general_logger.info('Log system activated')
        if self.model is not None:
            self.general_logger.info("Model initialization complete")
        sc = Scheduler(self.metrics_period, self.__scaling, autostart=False)
        th = Scheduler(self.metrics_period, self.__coordinate_threshold, autostart=False)
        sw = Scheduler(self.metrics_period, self.__coordinate_stabilization_window, autostart=False)

        threshold_coordinate_process = multiprocessing.Process(target=th.start)
        scaling_process = multiprocessing.Process(target=sc.start)
        stabilization_coordinate_process = multiprocessing.Process(target=sw.start)

        threshold_coordinate_process.start()
        scaling_process.start()
        stabilization_coordinate_process.start()

    def __scaling(self):
        with self.current_CDT_counter.get_lock():
            self.current_CDT_counter.value = self.current_CDT_counter.value - 1
            if self.current_CDT_counter.value < 1:
                self.current_CDT_counter.value = 0
        try:
            cpu_utilization = get_cpu_utilization(self.deployment_name, self.container_name, self.metrics_period)
            if cpu_utilization is not None:
                self.autoscaler_logger.info(f"Current CPU Utilization: {cpu_utilization}%")

                current_replicas = get_replicas(self.namespace, self.deployment_name, self.metrics_period)
                self.autoscaler_logger.info(f"Current Replicas: {current_replicas}")

                with self.target_cpu_utilization.get_lock():
                    desired_replicas = math.ceil((current_replicas * cpu_utilization) / self.target_cpu_utilization.value)
                desired_replicas = max(self.min_replicas, min(desired_replicas, self.max_replicas))
                self.autoscaler_logger.info(f"Desired Replicas: {desired_replicas}")

                with self.current_CDT_counter.get_lock():
                    if desired_replicas != current_replicas:
                        if desired_replicas > current_replicas:
                            set_replicas(self.namespace, self.deployment_name, desired_replicas)
                            with self.desired_CDT_counter.get_lock():
                                self.current_CDT_counter.value = self.desired_CDT_counter.value
                        else:
                            if self.current_CDT_counter.value < 1:
                                slope = get_new_stabilization_window_period(self.app_name, self.metrics_period)
                                if slope < 1: # -1 or 0
                                    set_replicas(self.namespace, self.deployment_name, desired_replicas)
                                    self.autoscaler_logger.info(f"Set Replicas to: {desired_replicas}")
                                with self.desired_CDT_counter.get_lock():
                                    self.current_CDT_counter.value = self.desired_CDT_counter.value
                    self.autoscaler_logger.info(f"Final CDT : {self.current_CDT_counter.value}")
            else:
                self.error_logger.error("Failed to get CPU utilization.")
        except Exception as e:
            self.error_logger.error(f"Scaling error: {str(e)}")
            
    def __coordinate_threshold(self):
        query = f'''sum(increase(istio_requests_total{{app="{self.app_name}"}}[{self.metrics_period}s])) by (app)'''
        try:
            latest_requests = get_prometheus_data(query, self.metrics_period)
            if latest_requests < 0 or latest_requests is None:
                latest_requests = 0

            if latest_requests == 0 and self.start_time is None and self.is_active == False: # when is before first, do nothing
                return
            self.is_active = True
            requests, is_stable = self.model.update_and_forecast(latest_requests)
            if is_stable == True:
                if self.start_time is None:
                    self.start_time = datetime.now()
                new_threshold = get_new_threshold(namespace=self.namespace, deployment_name=self.deployment_name, app_name=self.app_name, start_time=self.start_time, period=self.metrics_period, latest_requests=requests)
                self.autoscaler_logger.info(f"model forecast_data : {requests}")
                self.threshold_logger.info(f"new_threshold : {new_threshold[-1]}")
                with self.target_cpu_utilization.get_lock():
                    self.target_cpu_utilization.value = new_threshold[-1]
            else:
                self.threshold_logger.info('is not stable time')
        except Exception as e:
            self.error_logger.error(f"Threshold coordination error: {str(e)}")

    def __coordinate_stabilization_window(self):
        slope = get_new_stabilization_window_period(self.app_name, self.metrics_period)
        with self.desired_CDT_counter.get_lock():
            if slope > 0:
                self.desired_CDT_counter.value = min(self.desired_CDT_counter.value + 1, self.max_CDT_counter)
            elif slope < 0:
                self.desired_CDT_counter.value = max(self.desired_CDT_counter.value - 1, self.min_CDT_counter)
            
    def log_init(self):
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'log')
        os.makedirs(log_dir, exist_ok=True)
        self.general_logger = self.setup_logger('general_logger', 'general.log')
        self.error_logger = self.setup_logger('error_logger', 'error.log')
        self.autoscaler_logger = self.setup_logger('autoscaler_logger', 'autoscaler.log')
        self.threshold_logger = self.setup_logger('threshold_logger', 'threshold.log')
        self.CDT_logger = self.setup_logger('CDT_logger', 'CDT.log')
    
    def setup_logger(self, name, log_file, level=logging.INFO):
        handler = logging.FileHandler(os.path.join(log_dir, log_file))        
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)
    
        return logger
        
    def init_model(self):
        np.random.seed(42)
        mk = 10 
        lrate = 10**-(1)
        epsilon = 10**-(4)
        init_w = np.random.rand(mk) / 1000
        self.model = OnlineARIMA(mk=mk, lrate=lrate, init_w=init_w, epsilon=epsilon)
