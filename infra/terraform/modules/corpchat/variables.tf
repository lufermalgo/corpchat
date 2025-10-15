# Variables para el módulo CorpChat
# Permite desplegar la plataforma completa para un nuevo cliente

variable "project_id" {
  description = "GCP Project ID donde se desplegará CorpChat"
  type        = string
}

variable "region" {
  description = "GCP region para los recursos (ej. us-central1)"
  type        = string
  default     = "us-central1"
}

variable "client_name" {
  description = "Nombre del cliente (usado para prefijos de recursos)"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,28}[a-z0-9]$", var.client_name))
    error_message = "client_name debe ser lowercase, iniciar con letra, y contener solo letras, números y guiones"
  }
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment debe ser dev, staging, o prod"
  }
}

# Cloud Run Services
variable "gateway_image" {
  description = "Container image para Gateway service"
  type        = string
}

variable "ui_image" {
  description = "Container image para UI service"
  type        = string
}

variable "orchestrator_image" {
  description = "Container image para Orchestrator service"
  type        = string
}

variable "ingestor_image" {
  description = "Container image para Ingestor service"
  type        = string
}

# BigQuery
variable "bigquery_dataset_location" {
  description = "Location para BigQuery dataset"
  type        = string
  default     = "US"
}

variable "embedding_dimensions" {
  description = "Dimensiones de los embeddings (default: 768 para text-embedding-004)"
  type        = number
  default     = 768
}

# Compute
variable "gateway_cpu" {
  description = "CPU para Gateway service"
  type        = string
  default     = "1"
}

variable "gateway_memory" {
  description = "Memoria para Gateway service"
  type        = string
  default     = "1Gi"
}

variable "ui_cpu" {
  description = "CPU para UI service"
  type        = string
  default     = "1"
}

variable "ui_memory" {
  description = "Memoria para UI service"
  type        = string
  default     = "512Mi"
}

variable "orchestrator_cpu" {
  description = "CPU para Orchestrator service"
  type        = string
  default     = "1"
}

variable "orchestrator_memory" {
  description = "Memoria para Orchestrator service"
  type        = string
  default     = "1Gi"
}

variable "ingestor_cpu" {
  description = "CPU para Ingestor service"
  type        = string
  default     = "2"
}

variable "ingestor_memory" {
  description = "Memoria para Ingestor service"
  type        = string
  default     = "2Gi"
}

# Min/Max instances
variable "min_instances" {
  description = "Mínimo de instancias para servicios (0 para FinOps)"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Máximo de instancias para servicios"
  type        = number
  default     = 10
}

# GCS
variable "attachment_bucket_lifecycle_days" {
  description = "Días antes de mover attachments a Nearline storage"
  type        = number
  default     = 30
}

variable "attachment_bucket_deletion_days" {
  description = "Días antes de eliminar attachments (0 = nunca)"
  type        = number
  default     = 0
}

# IAP OAuth (opcional)
variable "enable_iap" {
  description = "Habilitar Identity-Aware Proxy"
  type        = bool
  default     = false
}

variable "iap_oauth_client_id" {
  description = "OAuth Client ID para IAP (requerido si enable_iap=true)"
  type        = string
  default     = ""
}

variable "iap_oauth_client_secret" {
  description = "OAuth Client Secret para IAP (requerido si enable_iap=true)"
  type        = string
  default     = ""
  sensitive   = true
}

# Labels
variable "additional_labels" {
  description = "Labels adicionales para todos los recursos"
  type        = map(string)
  default     = {}
}

