provider "kubernetes" {
  host                   = "https://${google_container_cluster.primary.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth.0.cluster_ca_certificate)
}

data "google_client_config" "default" {}

resource "kubernetes_namespace" "namespaces" {
  for_each = toset([var.namespace_scrape, var.namespace_train, var.namespace_infer])
  
  metadata {
    name = each.value
  }
  
  depends_on = [google_container_cluster.primary]
}

# Create service accounts for each namespace
resource "kubernetes_service_account" "scrape-service-account" {
  metadata {
    name      = "scrape-service-account"
    namespace = var.namespace_scrape
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.scrape-service-account.email
    }
  }
  
  depends_on = [kubernetes_namespace.namespaces]
}

resource "kubernetes_service_account" "train-service-account" {
  metadata {
    name      = "train-service-account"
    namespace = var.namespace_train
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.train-service-account.email
    }
  }
  
  depends_on = [kubernetes_namespace.namespaces]
}

resource "kubernetes_service_account" "infer-service-account" {
  metadata {
    name      = "infer-service-account"
    namespace = var.namespace_infer
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.infer-service-account.email
    }
  }
  
  depends_on = [kubernetes_namespace.namespaces]
}

resource "kubernetes_storage_class" "gcsfuse" {
  metadata {
    name = "gcsfuse"
  }

  storage_provisioner = "gcsfuse.csi.storage.gke.io"

  reclaim_policy        = "Retain"
  volume_binding_mode   = "Immediate"
  allow_volume_expansion = true
}

resource "kubernetes_persistent_volume" "gcs_fuse_pv" {
  metadata {
    name = "gcs-fuse-csi-pv"
  }

  spec {
    access_modes = ["ReadWriteMany"]

    capacity = {
      storage = "5Gi"
    }

    mount_options = ["implicit-dirs"]

    persistent_volume_source {
      csi {
        driver        = "gcsfuse.csi.storage.gke.io"
        volume_handle = "podcast-chiclets"  # Must be your GCS bucket name
      }
    }

    storage_class_name = "gcsfuse" # Optional, if you define this StorageClass manually
  }

  depends_on = [google_container_cluster.primary]
}

resource "kubernetes_persistent_volume_claim" "gcs_fuse_pvc" {
  metadata {
    name      = "gcs-fuse-csi-static-pvc"
    namespace = var.namespace_scrape
  }

  spec {
    access_modes = ["ReadWriteMany"]

    resources {
      requests = {
        storage = "5Gi"
      }
    }

    storage_class_name = "gcsfuse"  # Must match the PV if used
  }

  depends_on = [kubernetes_persistent_volume.gcs_fuse_pv]
}

resource "kubernetes_job" "buzz_scraper_job" {
  metadata {
    name      = "webscraper-job"
    namespace = var.namespace_scrape
  }

  spec {
    backoff_limit             = 2
    ttl_seconds_after_finished = 86400

    template {
      metadata {
        annotations = {
          "gke-gcsfuse/volumes" = "true"
        }
      }

      spec {
        service_account_name = "scrape-service-account"
        restart_policy       = "Never"

        node_selector = {
          "cloud.google.com/gke-nodepool" = "cpu-pool"
        }

        container {
          name  = "buzz-scraper"
          image = "us-east4-docker.pkg.dev/amlc-449423/amlcfinalproject/buzz-scraper:latest"

          env {
            name  = "PODCAST_CHICLETS"
            value = "/mnt/gcs"
          }

          env {
            name  = "PYTHONUNBUFFERED"
            value = "1"
          }

          volume_mount {
            name       = "podcast-chiclets"
            mount_path = "/mnt/gcs"
          }
        }

        volume {
          name = "podcast-chiclets"

          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.gcs_fuse_pvc.metadata[0].name
          }
        }
      }
    }
  }

  depends_on = [kubernetes_persistent_volume_claim.gcs_fuse_pvc]
}