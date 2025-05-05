#create service accounts for each namespace
resource "google_service_account" "scrape-service-account" {
  account_id = "scrape-service-account" 
}
resource "google_service_account" "train-service-account" {
  account_id = "train-service-account" 
}
resource "google_service_account" "infer-service-account" {
  account_id = "infer-service-account" 
}


locals {
  roles = [
    "roles/storage.admin",
    "roles/storage.objectViewer",
    "roles/artifactregistry.reader",
  ]
}

#grant storage admin to service accounts
resource "google_project_iam_member" "scrape_roles" {
  for_each = toset(local.roles)
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.scrape-service-account.email}"
}
resource "google_project_iam_member" "train-storage-admin" {
  for_each = toset(local.roles)
  project   = var.project_id
  role      = "roles/storage.admin"
  member    = "serviceAccount:${google_service_account.train-service-account.email}"
}
resource "google_project_iam_member" "infer-storage-admin" {
  for_each = toset(local.roles)
  project   = var.project_id
  role      = "roles/storage.admin"
  member    = "serviceAccount:${google_service_account.infer-service-account.email}"
}

#link kubernetes SAs to GCP SAs via workload identity
resource "google_service_account_iam_member" "scrape-workload-identity" {
  service_account_id    = google_service_account.scrape-service-account.id
  role                  = "roles/iam.workloadIdentityUser"
  member                = "serviceAccount:${var.project_id}.svc.id.goog[${var.namespace_scrape}/scrape-service-account]"
}
resource "google_service_account_iam_member" "train-workload-identity" {
  service_account_id    = google_service_account.train-service-account.id
  role                  = "roles/iam.workloadIdentityUser"
  member                = "serviceAccount:${var.project_id}.svc.id.goog[${var.namespace_train}/train-service-account]"
}
resource "google_service_account_iam_member" "infer-workload-identity" {
  service_account_id    = google_service_account.infer-service-account.id
  role                  = "roles/iam.workloadIdentityUser"
  member                = "serviceAccount:${var.project_id}.svc.id.goog[${var.namespace_infer}/infer-service-account]"
}

#grant to node-pool service account
resource "google_project_iam_member" "node_artifact_registry_access" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.kubernetes.email}"
}