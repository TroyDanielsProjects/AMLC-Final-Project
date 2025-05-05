#!/bin/bash

gcloud auth application-default login
gcloud storage buckets create gs://gemma-tfstate
gcloud storage rm -r gs://gemma-tfstate/terraform/state

terraform init

terraform apply

#need for kubectl
gcloud container clusters get-credentials $(terraform output -raw cluster_name) \
  --zone $(terraform output -raw zone)
