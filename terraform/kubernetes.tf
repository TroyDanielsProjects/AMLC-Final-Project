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
        volume_handle = "gemma-scraping"  # Must be your GCS bucket name
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
    backoff_limit             = 0
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
            name  = "GEMMA-SCRAPING"
            value = "/mnt/gcs"
          }

          env {
            name  = "PYTHONUNBUFFERED"
            value = "1"
          }

          volume_mount {
            name       = "gemma-scraping"
            mount_path = "/mnt/gcs"
          }
        }

        volume {
          name = "gemma-scraping"

          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.gcs_fuse_pvc.metadata[0].name
          }
        }
      }
    }
  }

  depends_on = [kubernetes_persistent_volume_claim.gcs_fuse_pvc]
}

resource "kubernetes_job" "podcast_scraper_job" {
  metadata {
    name      = "podscraper-job"
    namespace = var.namespace_scrape
  }

  spec {
    backoff_limit             = 0
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
          name  = "pod-scraper"
          image = "us-east4-docker.pkg.dev/amlc-449423/amlcfinalproject/podcast-scraper:latest"

          env {
            name  = "GEMMA-SCRAPING"
            value = "/mnt/gcs"
          }

          env {
            name  = "PYTHONUNBUFFERED"
            value = "1"
          }

          volume_mount {
            name       = "gemma-scraping"
            mount_path = "/mnt/gcs"
          }
        }

        volume {
          name = "gemma-scraping"

          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.gcs_fuse_pvc.metadata[0].name
          }
        }
      }
    }
  }

  depends_on = [kubernetes_persistent_volume_claim.gcs_fuse_pvc]
}


resource "kubernetes_job" "gemma_train_job" {
  metadata {
    name      = "gemma-train-job"
    namespace = "training"
  }

  spec {
    backoff_limit              = 0
    ttl_seconds_after_finished = 86400

    template {
      metadata {
        annotations = {
          "gke-gcsfuse/volumes" = "true"
        }
      }

      spec {
        service_account_name = "train-service-account"
        restart_policy       = "Never"

        node_selector = {
          "cloud.google.com/gke-nodepool" = "gke-gpu-pool-1"
        }

        toleration {
          key      = "nvidia.com/gpu"
          operator = "Equal"
          value    = "present"
          effect   = "NoSchedule"
        }

        container {
          name  = "gemma-train"
          image = "us-east4-docker.pkg.dev/amlc-449423/amlcfinalproject/gemma-train:latest"

          resources {
            limits = {
              "nvidia.com/gpu" = "1"
            }
          }

          env {
            name  = "MODEL_DIR"
            value = "/mnt/gemma-ft-models"
          }

          env {
            name  = "SCRAPING_DIR"
            value = "/mnt/gemma-scraping"
          }

          env {
            name  = "PYTHONUNBUFFERED"
            value = "1"
          }

          volume_mount {
            name       = "scraping-bucket"
            mount_path = "/mnt/gemma-scraping"
          }
        }

        volume {
          name = "scraping-bucket"

          csi {
            driver = "gcsfuse.csi.storage.gke.io"
            read_only = false
            volume_attributes = {
              bucketName   = "gemma-scraping"
              mountOptions = "implicit-dirs"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_deployment" "gemma_infer" {
  metadata {
    name = "gemma-infer-deployment"
    namespace = "inference"

    labels = {
      app = "gemma-infer"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "gemma-infer"
      }
    }

    template {
      metadata {
        labels = {
          app = "gemma-infer"
        }
        annotations = {
          "gke-gcsfuse/volumes" = "true"
        }
      }

      spec {
        service_account_name = "infer-service-account"

        container {
          name  = "gemma-infer-container"
          image = "us-east4-docker.pkg.dev/amlc-449423/amlcfinalproject/gemma-infer"

          port {
            container_port = 8080
          }

          volume_mount {
            name       = "scraping-bucket"
            mount_path = "/mnt/gemma-scraping"
          }
        }

        volume {
          name = "scraping-bucket"

          csi {
            driver = "gcsfuse.csi.storage.gke.io"
            read_only = true
            volume_attributes = {
              bucketName   = "gemma-scraping"
              mountOptions = "implicit-dirs"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "gemma_infer" {
  metadata {
    name = "gemma-infer-service"
    namespace = "inference"
  }

  spec {
    selector = {
      app = "gemma-infer"
    }

    type = "LoadBalancer"

    port {
      port        = 8080
      target_port = 8080
      node_port   = 30002
      protocol    = "TCP"
    }
  }
}
