from api.metrics import get_prometheus_data_all_list
import pandas as pd
import numpy as np

def __get_requests_metrics_list(app_name, start_time, period):
    """
    Fetches a list of request metrics for a given application from Prometheus.

    Parameters:
    app_name (str): The name of the application to get request metrics for.
    start_time (datetime): The start time for the query range.
    period (int): The period in seconds for each query interval.

    Returns:
    list: A list of request counts over the specified period.
    """
    query = f'''sum(increase(istio_requests_total{{app="{app_name}"}}[{period}s])) by (app)'''
    requests = get_prometheus_data_all_list(query=query, start_time=start_time, period=period)
    requests_list = [float(entry[1]) for entry in requests[0]['values'][1:]]
    return requests_list

def __get_z_score(requests_list):
    """
    Calculates the z-scores for the differences in request metrics.

    Parameters:
    requests_list (list): A list of request counts.

    Returns:
    pd.Series: A series of z-scores.
    """
    requests_series = pd.Series(requests_list)
    diff_requests_series = requests_series.diff().abs().rolling(window=10).mean()

    mean_diff = diff_requests_series.mean()
    std_diff = diff_requests_series.std()
    z_scores = (diff_requests_series - mean_diff) / std_diff
    z_scores = z_scores.fillna(0)
    return z_scores

def __reverse_sigmoid(x):
    """
    Applies a reverse sigmoid function to the input value.

    Parameters:
    x (float): The input value.

    Returns:
    float: The transformed value.
    """
    return 50 + 45 * (1 - (1 / (1 + np.exp(-x))))

def get_new_threshold(app_name, start_time, period, latest_requests):
    """
    Calculates a new threshold based on the z-scores of request metrics.

    Parameters:
    namespace (str): The namespace of the application.
    deployment_name (str): The deployment name of the application.
    app_name (str): The name of the application.
    start_time (datetime): The start time for the query range.
    period (int): The period in seconds for each query interval.
    latest_requests (float): The latest request count.

    Returns:
    list: A list of reverse sigmoid-transformed z-scores.
    """
    requests_list = __get_requests_metrics_list(app_name, start_time, period)
    requests_list.append(latest_requests)
    z_score_list = __get_z_score(requests_list)
    reverse_sigmoids = __reverse_sigmoid(z_score_list).tolist()
    return reverse_sigmoids
