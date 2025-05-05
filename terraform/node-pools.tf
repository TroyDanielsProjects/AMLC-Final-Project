#dedicated service account
resource "google_service_account" "kubernetes" {
  account_id = "kubernetes"
}

resource "google_container_node_pool" "general" {
  name = var.cpu_pool
  location = var.zone
  cluster = google_container_cluster.primary.id
  node_count = 3
  
  management {
    auto_repair  = "true"
    auto_upgrade = "true"
  }
  
  autoscaling {
    min_node_count = 1
    max_node_count = 3
  }

  node_config {
    image_type = "UBUNTU_CONTAINERD"
    preemptible = false
    machine_type = var.cpu_machine
    service_account = google_service_account.kubernetes.email
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    
    labels = {
      role = "general"
    }

  }
}

resource "google_container_node_pool" "gpu_pool" {
  name = var.gpu_pool
  location= var.zone
  cluster = google_container_cluster.primary.id
  node_count = 1

  management {
    auto_repair  = "true"
    auto_upgrade = "true"
  }

  autoscaling {
    min_node_count = 1
    max_node_count = 2
  }

  node_config {
    image_type = "UBUNTU_CONTAINERD"
    preemptible = false
    machine_type = var.gpu_machine
    disk_size_gb = 100
    disk_type = "pd-balanced"
    local_ssd_count = 0
    service_account = google_service_account.kubernetes.email
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    guest_accelerator {
        type = var.gpu_type
        count= var.gpu_count
    }
    
    metadata = {
      "install-nvidia-driver" = "true"
    }
    
    #avoid accidental scheduling
    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
  }
}
