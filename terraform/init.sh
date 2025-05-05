#!/bin/bash

docker buildx build   --platform=linux/amd64   -t us-east4-docker.pkg.dev/amlc-449423/amlcfinalproject/buzz-scraper:latest   --push ./../buzz_data
docker buildx build   --platform=linux/amd64   -t us-east4-docker.pkg.dev/amlc-449423/amlcfinalproject/podcast-scraper:latest   --push ./../podcast_scraper
docker buildx build   --platform=linux/amd64   -t us-east4-docker.pkg.dev/amlc-449423/amlcfinalproject/gemma-train:latest   --push ./../trainer

gcloud auth application-default login
gcloud storage buckets create gs://gemma-tfstate
gcloud storage buckets create gs://gemma-scraping
gcloud storage rm -r gs://gemma-tfstate/terraform/state

terraform init 

#use terraform to set up cluster, node pools, pvc
#also runs jobs (uses google beta for gcs fuse for bucket mounting)
terraform apply

#need for kubectl
gcloud container clusters get-credentials $(terraform output -raw cluster_name) \
  --zone $(terraform output -raw zone)