provider "kubernetes" {
  host                   = "https://${google_container_cluster.primary.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth.0.cluster_ca_certificate)
}

data "google_client_config" "default" {}

resource "kubernetes_namespace" "namespaces" {
  for_each = toset([var.namespace1, var.namespace2, var.namespace3])
  
  metadata {
    name = each.value
  }
  
  depends_on = [google_container_cluster.primary]
}

# Create the Kubernetes service account that will be bound to the Google service account
resource "kubernetes_service_account" "service-a" {
  metadata {
    name      = "service-a"
    namespace = var.namespace1
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.service-a.email
    }
  }
  
  depends_on = [kubernetes_namespace.namespaces]
}
