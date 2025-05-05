resource "google_container_cluster" "primary" {
  provider = google-beta  
  name     = var.cluster_name
  location = var.zone
  remove_default_node_pool = true
  initial_node_count = 1
  #monitoring_service = "prometheus"
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
    # Enable the GCS‑Fuse CSI driver
  addons_config {
    gcs_fuse_csi_driver_config {
      enabled = true
    }
  }
  # Make sure you pick a GKE version ≥ 1.24 (the driver is GA from 1.24)
  release_channel {
    channel = "REGULAR"
  }
}