#!/bin/bash
source ./env.sh

gcloud container node-pools create scraping-pool \
  --machine-type=n2-standard-2 \
  --num-nodes=3 \
  --location=$ZONE \
  --cluster=$CLUSTER_NAME \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5 \
  --num-nodes=1 \