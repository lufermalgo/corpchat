# Variables para el deployment del cliente

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "client_name" {
  description = "Nombre del cliente (lowercase, sin espacios)"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Container images
variable "gateway_image" {
  description = "Container image para Gateway"
  type        = string
}

variable "ui_image" {
  description = "Container image para UI"
  type        = string
}

variable "orchestrator_image" {
  description = "Container image para Orchestrator"
  type        = string
}

variable "ingestor_image" {
  description = "Container image para Ingestor"
  type        = string
}

