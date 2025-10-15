# Ejemplo de deployment de CorpChat para un cliente específico
# Copiar este directorio y ajustar variables para cada nuevo cliente

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Descomentar para usar backend remoto (GCS)
  # backend "gcs" {
  #   bucket = "terraform-state-corpchat"
  #   prefix = "clients/example-client"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Llamada al módulo CorpChat
module "corpchat" {
  source = "../../modules/corpchat"

  # Configuración del cliente
  project_id   = var.project_id
  region       = var.region
  client_name  = var.client_name
  environment  = var.environment

  # Container images (desde Artifact Registry)
  gateway_image      = var.gateway_image
  ui_image           = var.ui_image
  orchestrator_image = var.orchestrator_image
  ingestor_image     = var.ingestor_image

  # Compute resources (ajustar según necesidades del cliente)
  gateway_cpu         = "1"
  gateway_memory      = "1Gi"
  ui_cpu              = "1"
  ui_memory           = "512Mi"
  orchestrator_cpu    = "1"
  orchestrator_memory = "1Gi"
  ingestor_cpu        = "2"
  ingestor_memory     = "2Gi"

  # Scaling (ajustar para FinOps)
  min_instances = 0
  max_instances = 10

  # Storage lifecycle
  attachment_bucket_lifecycle_days = 30  # Mover a Nearline después de 30 días
  attachment_bucket_deletion_days  = 0   # 0 = nunca eliminar (ajustar según retención)

  # BigQuery
  bigquery_dataset_location = "US"
  embedding_dimensions      = 768

  # IAP (opcional)
  enable_iap = false

  # Labels adicionales
  additional_labels = {
    cost_center = "engineering"
    team        = "platform"
  }
}

