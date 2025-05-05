#!/bin/bash

gcloud auth application-default login
gcloud storage buckets create gs://gemma-tfstate

terraform init

# 3. Apply Terraform — this creates the cluster, node pools, etc.
terraform apply

# 4. Configure kubectl to talk to your new cluster
gcloud container clusters get-credentials $(terraform output -raw cluster_name) \
  --zone $(terraform output -raw zone)
