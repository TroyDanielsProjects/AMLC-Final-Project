#!/bin/bash
source ./env.sh

gcloud projects add-iam-policy-binding $PROJECT_ID\
  --role=roles/storage.admin \
  --role=roles/iam.workloadIdentityUser \
  --role="roles/storage.objectViewer" \
  --role="roles/artifactregistry.reader" \
  --member="serviceAccount:$SERVICE_ACC"