from kubernetes import client, config
from kubernetes.client.rest import ApiException
from api.metrics import get_prometheus_data


def get_cpu_utilization(deployment_name, container_name, period=60):
    """
    Fetches the CPU utilization for a given deployment and container from Prometheus.

    Parameters:
    deployment_name (str): The deployment name of the application.
    container_name (str): The container name within the deployment.
    period (int, optional): The period over which to fetch metrics. Default is 60.

    Returns:
    float: The CPU utilization percentage.
    """
    query = f'''(sum(rate(container_cpu_usage_seconds_total{{cpu="total",pod=~"{deployment_name}-.*",container="{container_name}"}}[{period}s])) * 1000)  / (sum(container_spec_cpu_quota{{container="{container_name}"}} / 100)) * 100'''

    try:
        result = get_prometheus_data(query=query, period=period)
        return result
    except Exception as e:
        raise Exception(f"Error querying Prometheus: {e}")
        

def set_replicas(namespace, deployment_name, replicas):
    """
    Sets the number of replicas for a given deployment.

    Parameters:
    namespace (str): The namespace of the application.
    deployment_name (str): The deployment name of the application.
    replicas (int): The desired number of replicas.

    Returns:
    None
    """
    # Load Kubernetes cluster configuration
    config.load_incluster_config()
    # 
    # Create Kubernetes API client
    v1 = client.AppsV1Api()
    if replicas < 1:
        replicas = 1
    replicas = int(replicas)
    body = {'spec': {'replicas': replicas}}
    try:
        v1.patch_namespaced_deployment_scale(deployment_name, namespace, body)
    except ApiException as e:
        raise Exception(f"Error setting replicas: {e}")

def get_replicas(namespace, deployment, period=60):
    """
    Gets the current number of replicas for a given deployment.

    Parameters:
    namespace (str): The namespace of the application.
    deployment (str): The deployment name of the application.
    period (int, optional): The period over which to fetch metrics. Default is 60.

    Returns:
    int: The current number of replicas.
    """
    query = f'''kube_deployment_status_replicas{{deployment="{deployment}", namespace="{namespace}"}}'''
    try:
        replicas = int(get_prometheus_data(query=query, period=period))
        if replicas == 0:
            replicas = 1
        return replicas
    except Exception as e:
        raise Exception(f"Error querying Prometheus: {e}")
