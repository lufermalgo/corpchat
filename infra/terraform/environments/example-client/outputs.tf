# Outputs del deployment del cliente

output "deployment_summary" {
  description = "Resumen completo del deployment"
  value       = module.corpchat.deployment_summary
}

output "gateway_url" {
  description = "URL del Gateway (OpenAI-compatible API)"
  value       = module.corpchat.gateway_url
}

output "ui_url" {
  description = "URL de la UI (Open WebUI)"
  value       = module.corpchat.ui_url
}

output "orchestrator_url" {
  description = "URL del Orchestrator (ADK Multi-Agent)"
  value       = module.corpchat.orchestrator_url
}

output "ingestor_url" {
  description = "URL del Ingestor (Document Processing)"
  value       = module.corpchat.ingestor_url
}

output "service_account_email" {
  description = "Service Account para los servicios"
  value       = module.corpchat.service_account_email
}

output "attachments_bucket" {
  description = "Bucket de GCS para attachments"
  value       = module.corpchat.attachments_bucket_name
}

output "bigquery_table" {
  description = "Tabla de BigQuery para embeddings"
  value       = module.corpchat.bigquery_table_full_id
}

