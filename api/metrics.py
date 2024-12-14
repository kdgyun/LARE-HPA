from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta
import os

prometheus_ip = os.getenv('PROMETHEUS_IP', "")

# Configure Prometheus client
prom = PrometheusConnect(url=prometheus_ip, disable_ssl=True)

def get_prometheus_data(query, period):
    """
    Fetches the latest metric value from Prometheus for a given query over a specified period.

    Parameters:
    query (str): The Prometheus query.
    period (int): The period in seconds for each query interval.

    Returns:
    float: The latest value of the metric. Returns 0.0 if no result is found.
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(seconds=period)
    result = prom.custom_query_range(
        query=query,
        start_time=start_time,
        end_time=end_time,
        step=f"{period}s"
    )
    if result:
        return float(result[0]['values'][-1][1])
    else:
        return 0.0

def get_prometheus_data_all_list(query, start_time, period):
    """
    Fetches a list of metric values from Prometheus for a given query starting from a specified time.

    Parameters:
    query (str): The Prometheus query.
    start_time (datetime): The start time for the query range.
    period (int): The period in seconds for each query interval.

    Returns:
    list: A list of metric values over the specified range.
    """
    end_time = datetime.now()
    result = prom.custom_query_range(
        query=query,
        start_time=start_time,
        end_time=end_time,
        step=f"{period}s"
    )
    return result

def get_prometheus_data_n_times_list(query, period, n_times):
    """
    Fetches a list of metric values from Prometheus for a given query over a specified number of periods.

    Parameters:
    query (str): The Prometheus query.
    period (int): The period in seconds for each query interval.
    n_times (int): The number of intervals to fetch.

    Returns:
    list: A list of metric values over the specified number of intervals.
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(seconds=period * n_times)
    result = prom.custom_query_range(
        query=query,
        start_time=start_time,
        end_time=end_time,
        step=f"{period}s"
    )
    return result
