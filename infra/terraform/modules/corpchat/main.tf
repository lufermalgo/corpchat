# Módulo Terraform para CorpChat Multi-Cliente
# Despliega infraestructura completa para un cliente

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

locals {
  service_prefix = "${var.client_name}-corpchat"
  common_labels = merge(
    {
      client      = var.client_name
      environment = var.environment
      managed_by  = "terraform"
      platform    = "corpchat"
    },
    var.additional_labels
  )
}

# Service Account para los servicios
resource "google_service_account" "corpchat_app" {
  account_id   = "${local.service_prefix}-app"
  display_name = "CorpChat Application Service Account (${var.client_name})"
  project      = var.project_id
}

# IAM Roles para Service Account
resource "google_project_iam_member" "corpchat_app_roles" {
  for_each = toset([
    "roles/aiplatform.user",           # Vertex AI
    "roles/bigquery.dataEditor",       # BigQuery
    "roles/bigquery.jobUser",          # BigQuery Jobs
    "roles/datastore.user",            # Firestore
    "roles/storage.objectViewer",      # GCS Read
    "roles/logging.logWriter",         # Cloud Logging
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.corpchat_app.email}"
}

# GCS Bucket para attachments
resource "google_storage_bucket" "attachments" {
  name          = "${local.service_prefix}-${var.project_id}-attachments"
  project       = var.project_id
  location      = var.region
  force_destroy = var.environment == "dev" ? true : false

  uniform_bucket_level_access = true

  versioning {
    enabled = var.environment == "prod" ? true : false
  }

  lifecycle_rule {
    condition {
      age = var.attachment_bucket_lifecycle_days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  dynamic "lifecycle_rule" {
    for_each = var.attachment_bucket_deletion_days > 0 ? [1] : []
    content {
      condition {
        age = var.attachment_bucket_deletion_days
      }
      action {
        type = "Delete"
      }
    }
  }

  labels = local.common_labels
}

# IAM para bucket - Service Account
resource "google_storage_bucket_iam_member" "attachments_object_admin" {
  bucket = google_storage_bucket.attachments.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.corpchat_app.email}"
}

# BigQuery Dataset
resource "google_bigquery_dataset" "corpchat" {
  dataset_id    = "${replace(var.client_name, "-", "_")}_corpchat"
  project       = var.project_id
  location      = var.bigquery_dataset_location
  friendly_name = "CorpChat ${var.client_name} - Vector Store"
  description   = "Vector embeddings y metadata para RAG - Cliente: ${var.client_name}"

  labels = local.common_labels
}

# BigQuery Table para embeddings
resource "google_bigquery_table" "embeddings" {
  dataset_id          = google_bigquery_dataset.corpchat.dataset_id
  table_id            = "embeddings"
  project             = var.project_id
  deletion_protection = var.environment == "prod" ? true : false

  time_partitioning {
    type  = "DAY"
    field = "created_at"
  }

  clustering = ["user_id", "chat_id"]

  schema = jsonencode([
    {
      name        = "embedding_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "UUID del embedding"
    },
    {
      name        = "attachment_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "ID del attachment procesado"
    },
    {
      name        = "chat_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "ID del chat"
    },
    {
      name        = "user_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "ID del usuario"
    },
    {
      name        = "chunk_index"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Índice del chunk en el documento"
    },
    {
      name        = "chunk_text"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Texto del chunk"
    },
    {
      name        = "embedding"
      type        = "FLOAT"
      mode        = "REPEATED"
      description = "Vector embedding (768 dimensiones)"
    },
    {
      name        = "metadata"
      type        = "JSON"
      mode        = "NULLABLE"
      description = "Metadata adicional del chunk"
    },
    {
      name        = "created_at"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Timestamp de creación"
    }
  ])

  labels = local.common_labels
}

# Cloud Run Services
# Gateway
resource "google_cloud_run_v2_service" "gateway" {
  name     = "${local.service_prefix}-gateway"
  project  = var.project_id
  location = var.region

  template {
    service_account = google_service_account.corpchat_app.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.gateway_image

      resources {
        limits = {
          cpu    = var.gateway_cpu
          memory = var.gateway_memory
        }
      }

      env {
        name  = "VERTEX_PROJECT"
        value = var.project_id
      }
      env {
        name  = "VERTEX_LOCATION"
        value = var.region
      }
      env {
        name  = "MODEL"
        value = "gemini-2.5-flash-001"
      }
    }

    labels = local.common_labels
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# UI
resource "google_cloud_run_v2_service" "ui" {
  name     = "${local.service_prefix}-ui"
  project  = var.project_id
  location = var.region

  template {
    service_account = google_service_account.corpchat_app.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.ui_image

      resources {
        limits = {
          cpu    = var.ui_cpu
          memory = var.ui_memory
        }
      }
    }

    labels = local.common_labels
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Orchestrator
resource "google_cloud_run_v2_service" "orchestrator" {
  name     = "${local.service_prefix}-orchestrator"
  project  = var.project_id
  location = var.region

  template {
    service_account = google_service_account.corpchat_app.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.orchestrator_image

      resources {
        limits = {
          cpu    = var.orchestrator_cpu
          memory = var.orchestrator_memory
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = google_bigquery_dataset.corpchat.dataset_id
      }
    }

    labels = local.common_labels
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Ingestor
resource "google_cloud_run_v2_service" "ingestor" {
  name     = "${local.service_prefix}-ingestor"
  project  = var.project_id
  location = var.region

  template {
    service_account = google_service_account.corpchat_app.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    timeout = "900s"

    containers {
      image = var.ingestor_image

      resources {
        limits = {
          cpu    = var.ingestor_cpu
          memory = var.ingestor_memory
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = google_bigquery_dataset.corpchat.dataset_id
      }
      env {
        name  = "GCS_BUCKET"
        value = google_storage_bucket.attachments.name
      }
    }

    labels = local.common_labels
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# IAM para permitir invocaciones autenticadas
resource "google_cloud_run_v2_service_iam_member" "gateway_invoker" {
  name    = google_cloud_run_v2_service.gateway.name
  project = var.project_id
  location = var.region
  role    = "roles/run.invoker"
  member  = "allAuthenticatedUsers"
}

resource "google_cloud_run_v2_service_iam_member" "ui_invoker" {
  name    = google_cloud_run_v2_service.ui.name
  project = var.project_id
  location = var.region
  role    = "roles/run.invoker"
  member  = "allAuthenticatedUsers"
}

resource "google_cloud_run_v2_service_iam_member" "orchestrator_invoker" {
  name    = google_cloud_run_v2_service.orchestrator.name
  project = var.project_id
  location = var.region
  role    = "roles/run.invoker"
  member  = "allAuthenticatedUsers"
}

resource "google_cloud_run_v2_service_iam_member" "ingestor_invoker" {
  name    = google_cloud_run_v2_service.ingestor.name
  project = var.project_id
  location = var.region
  role    = "roles/run.invoker"
  member  = "allAuthenticatedUsers"
}

