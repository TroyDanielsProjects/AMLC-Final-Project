provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.primary.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth.0.cluster_ca_certificate)
  }
}

# Create a namespace for monitoring
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
  
  depends_on = [google_container_cluster.primary]
}

# Deploy Prometheus using Helm
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  
  set {
    name  = "server.persistentVolume.enabled"
    value = "true"
  }
  
  set {
    name  = "server.persistentVolume.size"
    value = "10Gi"
  }
  
  set {
    name  = "alertmanager.persistentVolume.enabled"
    value = "true"
  }
  
  depends_on = [kubernetes_namespace.monitoring]
}

# Deploy Grafana using Helm
resource "helm_release" "grafana" {
  name       = "grafana"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  
  set {
    name  = "persistence.enabled"
    value = "true"
  }
  
  set {
    name  = "persistence.size"
    value = "5Gi"
  }
  
  set {
    name  = "service.type"
    value = "LoadBalancer"
  }
  
  # Configure Grafana to use Prometheus as a data source
  set {
    name  = "datasources.datasources\\.yaml.apiVersion"
    value = "1"
  }
  
  set {
    name  = "datasources.datasources\\.yaml.datasources[0].name"
    value = "Prometheus"
  }
  
  set {
    name  = "datasources.datasources\\.yaml.datasources[0].type"
    value = "prometheus"
  }
  
  set {
    name  = "datasources.datasources\\.yaml.datasources[0].url"
    value = "http://prometheus-server.monitoring.svc.cluster.local"
  }
  
  set {
    name  = "datasources.datasources\\.yaml.datasources[0].access"
    value = "proxy"
  }
  
  set {
    name  = "datasources.datasources\\.yaml.datasources[0].isDefault"
    value = "true"
  }
  
  depends_on = [helm_release.prometheus]
}

# Output the Grafana service endpoint
output "grafana_endpoint" {
  value = "kubectl get svc grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
  description = "Command to get the Grafana dashboard endpoint"
}
