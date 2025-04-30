#!/bin/bash
source ./env.sh

kubectl apply -f ../yamlfiles/volume.yaml
kubectl apply -f ../yamlfiles/volumeClaim.yaml
kubectl apply -f ../yamlfiles/buzz-job.yaml