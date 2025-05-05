#!/bin/bash

source ./env.sh
bash gcloud auth login
bash create-cluster.sh
bash create-cpu-pool.sh
bash create-news-job.sh
bash create-podcast-job.sh



bash iam-default.sh
bash create-gpu-pool.sh
#bash create-train-job.sh