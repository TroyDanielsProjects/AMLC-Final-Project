variable "project_id"{
  type = string
}

variable "cluster_name" {
  type = string
}

variable "region" {
  type = string
}

variable "zone" {
  type = string
}

variable "gpu_type" {
  type = string
}

variable "gpu_count" {
  type = number
}

variable "gpu_machine" {
  type = string
}

variable "gpu_pool" {
  type = string
}

variable "cpu_machine" {
  type =string
}

variable "cpu_pool" {
  type = string
}

variable "service_acc" {
  type = string
}

variable "namespace_scrape"{
    type = string
}
variable "namespace_train"{
    type = string
}
variable "namespace_infer"{
    type = string
}