#!/bin/bash
source ./env.sh

gcloud container node-pools describe $GPU_POOL \
  --cluster=$CLUSTER_NAME \
  --region=$ZONE 