#create service accounts for each namespace
resource "google_service_account" "scrape_service_account" {
  account_id = "scrape-service-account" 
}
resource "google_service_account" "train_service_account" {
  account_id = "train-service-account" 
}
resource "google_service_account" "infer_service_account" {
  account_id = "infer-service-account" 
}

#grant storage admin to service accounts
resource "google_project_iam_member" "scrape_storage_admin" {
  project   = var.project_id
  role      = "roles/storage.admin"
  member    = "serviceAccount:${google_service_account.scrape_service_account.email}"
}
resource "google_project_iam_member" "train_storage_admin" {
  project   = var.project_id
  role      = "roles/storage.admin"
  member    = "serviceAccount:${google_service_account.train_service_account.email}"
}
resource "google_project_iam_member" "infer_storage_admin" {
  project   = var.project_id
  role      = "roles/storage.admin"
  member    = "serviceAccount:${google_service_account.infer_service_account.email}"
}

#link kubernetes SAs to GCP SAs via workload identity
resource "google_service_account_iam_member" "scrape_workload_identity" {
  service_account_id    = google_service_account.scrape_service_account.id
  role                  = "roles/iam.workloadIdentityUser"
  member                = "serviceAccount:${var.project_id}.svc.id.goog[${var.namespace_scrape}/scrape-service-account]"
}
resource "google_service_account_iam_member" "train_workload_identity" {
  service_account_id    = google_service_account.train_service_account.id
  role                  = "roles/iam.workloadIdentityUser"
  member                = "serviceAccount:${var.project_id}.svc.id.goog[${var.namespace_train}/train-service-account]"
}
resource "google_service_account_iam_member" "infer_workload_identity" {
  service_account_id    = google_service_account.infer_service_account.id
  role                  = "roles/iam.workloadIdentityUser"
  member                = "serviceAccount:${var.project_id}.svc.id.goog[${var.namespace_infer}/infer-service-account]"
}