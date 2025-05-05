provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

terraform {
  #need bucket to store terraform state

  backend "gcs" {
    bucket = "gemma-tfstate"
    prefix = "terraform/state"
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.74.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
  }

  required_version = ">= 0.14"
}