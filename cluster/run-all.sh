#!/bin/bash

source ./env.sh
bash gcloud auth login
bash create-cluster.sh
bash create-node-pool.sh
bash iam-default.sh
bash create-buzz-job.sh
bash create-chiclets-job.sh
bash create-train-job.sh