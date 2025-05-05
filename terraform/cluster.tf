resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.zone
  remove_default_node_pool = true
  initial_node_count = 1
  #monitoring_service = "prometheus"
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}