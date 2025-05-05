#create service account
resource "google_service_account" "service-a" {
  account_id = "service-a" 
}

#grand storage admin to service-a service account
resource "google_project_iam_member" "service-a" {
  project   = var.project_id
  role      = "roles/storage.admin"
  member    = "serviceAccount:${google_service_account.service-a.email}"
}

#link kubernetes SA to GCP SA via workload identity
resource "google_service_account_iam_member" "service-a" {
  service_account_id    = google_service_account.service-a.id
  role                  = "roles/iam.workloadIdentityUser"
  member                = "serviceAccount:${var.project_id}.svc.id.goog[${var.namespace1}/service-a]"
}