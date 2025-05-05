#!/bin/bash
source ./env.sh

gcloud container clusters create $CLUSTER_NAME \
  --zone=$ZONE \
  --addons=GcsFuseCsiDriver \
  --num-nodes=1 \
  --workload-pool=$PROJECT_ID.svc.id.goog