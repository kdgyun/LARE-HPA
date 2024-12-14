#!/bin/bash

kubectl create namespace autoscale

kubectl apply -f ConfigMap.yaml -n autoscale

kubectl apply -f ClusterRole.yaml -n autoscale

kubectl apply -f Deployments.yaml -n autoscale

echo "Deployment completed successfully."
