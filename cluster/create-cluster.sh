#!/bin/bash
gcloud container clusters create $CLUSTER_NAME \
  --zone=$ZONE \
  --addons=GcsFuseCsiDriver \
  --machine-type=$MACHINE_TYPE \
  --num-nodes=1 \
  --workload-pool=$PROJECT_ID.svc.id.goog