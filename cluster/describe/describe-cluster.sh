#!/bin/bash
source ./env.sh

 gcloud container clusters describe $CLUSTER_NAME \
    --region=$ZONE