#!/bin/bash
source ./env.sh

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACC" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACC" \
  --role="roles/iam.workloadIdentityUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACC" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACC" \
  --role="roles/artifactregistry.reader"

gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACC \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${PROJECT_ID}.svc.id.goog[default/default]"


kubectl annotate serviceaccount default \
  -n default \
  iam.gke.io/gcp-service-account=$SERVICE_ACC