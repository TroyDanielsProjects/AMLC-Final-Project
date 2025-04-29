#!/bin/bash
CLUSTER_NAME="gemma-sft"
ZONE="us-east4-c"
MACHINE_TYPE="g2-standard-4"
PROJECT_ID="amlc-449423"

GPU="nvidia-l4"
GPU_COUNT="1"
GPU_POOL="gke-gpu-pool-1"
export PROJECT_ID ZONE MACHINE_TYPE PROJECT_ID GPU GPU_COUNT GPU_POOL



bash create_cluster.sh