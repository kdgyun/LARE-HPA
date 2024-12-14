# LARE-HPA: Co-optimizing Latency and Resource Efficiency for Kubernetes Autoscaling

LARE-HPA (**L**atency-**A**ware and **R**esource-**E**fficient Horizontal Pod Autoscaler) is an adaptive autoscaling solution designed to optimize the trade-off between latency and resource efficiency in Kubernetes. Unlike traditional HPA approaches, which rely on static thresholds, LARE-HPA dynamically adjusts thresholds and stabilization windows to handle workload volatility in real time.

## Requirements

- Ubuntu 20.04
- Docker version 27.3.1
- Kubernetes version 1.27.5
- Istio version 1.21.0
- Prometheus 2.54.0
- kube-state-metrics v2.7.0
- Python3 (tested on Python 3.11)

**Note:** The above setup has been tested with the specified versions. However, version dependencies may vary depending on the operating system and other installed programs.

## Get Started

### Prerequisites
LARE-HPA requires **Prometheus** and **Istio** to operate. Ensure that you select appropriate versions compatible with your cluster setup to collect metrics effectively. Once configured, deploy the target application for autoscaling, and generate sufficient load to verify that the metrics are being collected correctly.

### Deployment Steps
####  1. Build the Docker Image
Build the container image for LARE-HPA using Docker.

#### Update yamls/Deployments.yaml
Modify the following fields:
- **containers.image:** Replace <your-lare-hpa-image> with the local or remote path of your built LARE-HPA container image.
- **volumes.hostPath.path**: Specify the local path where logs will be stored.

#### Update yamls/ConfigMap.yaml
Configure the Prometheus endpoint and specify the scaling target application's details. Ensure that the Prometheus server is correctly exposing metrics for LARE-HPA to use.

#### Deploy LARE-HPA
Run the deployment script to deploy LARE-HPA into your Kubernetes cluster.

```bash
./deploy.sh
```

#### Verify Metrics and Scaling
Ensure that the target application metrics are being collected and that autoscaling is functioning as expected.

### Cleanup
To completely remove the scaler from your Kubernetes cluster, execute the following script:

```bash
./delete.sh
```

## Citation
If you find the provided code or the corresponding paper useful, please consider citing the paper:
