import numpy as np
from scipy import stats
from api.metrics import get_prometheus_data_n_times_list

def __get_requests_metrics_list(app_name, period):
    """
    Fetches a list of request metrics for a given application from Prometheus.

    Parameters:
    app_name (str): The name of the application to get request metrics for.
    period (int): The period over which to fetch metrics.

    Returns:
    list: A list of request counts over the specified period.
    """
    query = f'''sum(increase(istio_requests_total{{app="{app_name}"}}[{period}s])) by (app)'''
    requests = get_prometheus_data_n_times_list(query=query, period=period, n_times=60)
    requests_list = [float(entry[1]) if entry[1] is not None else 0 for entry in requests[0]['values'][1:]]
    return requests_list

def get_new_stabilization_window_period(app_name, period):
    """
    Retrieves the latest request count for the given application and determines the slope direction
    and whether scaling is allowed based on Durbin-Watson statistics.

    Parameters:
    app_name (str): The name of the application.
    period (int): The period over which to fetch metrics.
    
    Returns:
    int: The slope direction (1 for positive, 0 for zero, -1 for negative).
    """
    request_list = __get_requests_metrics_list(app_name, period)
    slope = __check_slope_and_dw(request_list)
    return slope

def __durbin_watson(residuals):
    """
    Calculates the Durbin-Watson statistic for a given set of residuals.

    Parameters:
    residuals (array-like): The residuals from a regression model.

    Returns:
    float: The Durbin-Watson statistic.
    """
    diff_residuals = np.diff(residuals)
    if np.sum(residuals**2) == 0:
        return 0
    dw_stat = np.sum(diff_residuals**2) / np.sum(residuals**2)
    return dw_stat

def __check_slope_and_dw(requests):
    """
    Checks the slope and Durbin-Watson statistic for the request metrics.

    Parameters:
    requests (array-like): The request counts over time.

    Returns:
    int: The slope direction (1 for positive, 0 for zero, -1 for negative).
    """
    X = np.arange(len(requests))
    y = np.array(requests)
    slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
    y_pred = intercept + slope * X
    residuals = y - y_pred

    dw = __durbin_watson(residuals)
    # a = .05, k = 1, n = 60 (based on statistical assumptions)
    if 1.616 <= dw <= 2.384:
        if slope > 0:
            return 1
        elif slope == 0:
            return 0
        else:
            return -1
    else:
        return 0
