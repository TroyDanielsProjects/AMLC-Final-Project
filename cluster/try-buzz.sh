# !/bin/bash

kubectl delete job webscraper-job
kubectl delete pvc gcs-fuse-csi-static-pvc
kubectl delete pv gcs-fuse-csi-pv
# Recreate them cleanly
kubectl apply -f pv.yaml
kubectl apply -f pvc.yaml
bash create-buzz-job.sh
kubectl get pods