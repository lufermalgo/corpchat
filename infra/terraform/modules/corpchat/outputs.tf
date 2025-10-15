# Outputs del módulo CorpChat

output "service_account_email" {
  description = "Email de la Service Account creada"
  value       = google_service_account.corpchat_app.email
}

output "attachments_bucket_name" {
  description = "Nombre del bucket de attachments"
  value       = google_storage_bucket.attachments.name
}

output "attachments_bucket_url" {
  description = "URL del bucket de attachments"
  value       = google_storage_bucket.attachments.url
}

output "bigquery_dataset_id" {
  description = "ID del dataset de BigQuery"
  value       = google_bigquery_dataset.corpchat.dataset_id
}

output "bigquery_table_id" {
  description = "ID de la tabla de embeddings"
  value       = google_bigquery_table.embeddings.table_id
}

output "bigquery_table_full_id" {
  description = "ID completo de la tabla (project.dataset.table)"
  value       = "${var.project_id}.${google_bigquery_dataset.corpchat.dataset_id}.${google_bigquery_table.embeddings.table_id}"
}

# Cloud Run Services URLs
output "gateway_url" {
  description = "URL del servicio Gateway"
  value       = google_cloud_run_v2_service.gateway.uri
}

output "ui_url" {
  description = "URL del servicio UI"
  value       = google_cloud_run_v2_service.ui.uri
}

output "orchestrator_url" {
  description = "URL del servicio Orchestrator"
  value       = google_cloud_run_v2_service.orchestrator.uri
}

output "ingestor_url" {
  description = "URL del servicio Ingestor"
  value       = google_cloud_run_v2_service.ingestor.uri
}

# Cloud Run Services Names
output "gateway_service_name" {
  description = "Nombre del servicio Gateway"
  value       = google_cloud_run_v2_service.gateway.name
}

output "ui_service_name" {
  description = "Nombre del servicio UI"
  value       = google_cloud_run_v2_service.ui.name
}

output "orchestrator_service_name" {
  description = "Nombre del servicio Orchestrator"
  value       = google_cloud_run_v2_service.orchestrator.name
}

output "ingestor_service_name" {
  description = "Nombre del servicio Ingestor"
  value       = google_cloud_run_v2_service.ingestor.name
}

# Summary
output "deployment_summary" {
  description = "Resumen del deployment"
  value = {
    client       = var.client_name
    environment  = var.environment
    project      = var.project_id
    region       = var.region
    services = {
      gateway      = google_cloud_run_v2_service.gateway.uri
      ui           = google_cloud_run_v2_service.ui.uri
      orchestrator = google_cloud_run_v2_service.orchestrator.uri
      ingestor     = google_cloud_run_v2_service.ingestor.uri
    }
    storage = {
      attachments_bucket = google_storage_bucket.attachments.name
      bigquery_dataset   = google_bigquery_dataset.corpchat.dataset_id
    }
  }
}

