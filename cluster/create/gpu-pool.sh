#!/bin/bash
source ./env.sh

gcloud container node-pools create $GPU_POOL \
  --accelerator=type=$GPU,count=$GPU_COUNT,gpu-driver-version=default \
  --machine-type=$MACHINE_TYPE \
  --num-nodes=1 \
  --location=$ZONE \
  --cluster=$CLUSTER_NAME \
  --workload-metadata=GKE_METADATA