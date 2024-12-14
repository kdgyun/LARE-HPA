from controllers.controller import HorizontalPodAutoscalerController
import os

if __name__ == "__main__":
    namespace = os.getenv('NAMESPACE')
    deployment_name = os.getenv('DEPLOYMENT')
    container_name = os.getenv('CONTAINER')
    app_name = os.getenv('APP_NAME')
    target_cpu_utilization = int(os.getenv('TARGET_CPU_UTILIZATION','75'))
    min_replicas = int(os.getenv('MIN_REPLICAS','1'))
    max_replicas = int(os.getenv('MAX_REPLICAS','15'))
    metric_period = int(os.getenv('METRIC_PERIOD', '30'))

    hpa = HorizontalPodAutoscalerController(namespace, deployment_name, app_name, container_name, target_cpu_utilization, min_replicas, max_replicas, metric_period)
    hpa.scale()
