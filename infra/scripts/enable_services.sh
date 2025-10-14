#!/bin/bash
set -euo pipefail

# Script para habilitar servicios de GCP necesarios para CorpChat MVP
# Proyecto: genai-385616

PROJECT_ID="${PROJECT_ID:-genai-385616}"
REGION="${REGION:-us-central1}"

echo "Habilitando servicios de GCP para el proyecto ${PROJECT_ID}..."

# Configurar proyecto activo
gcloud config set project "${PROJECT_ID}"
gcloud config set run/region "${REGION}"

# Lista de servicios a habilitar
SERVICES=(
    "run.googleapis.com"                    # Cloud Run
    "iap.googleapis.com"                    # Identity-Aware Proxy
    "secretmanager.googleapis.com"          # Secret Manager
    "aiplatform.googleapis.com"             # Vertex AI
    "firestore.googleapis.com"              # Firestore
    "storage.googleapis.com"                # Cloud Storage
    "cloudbuild.googleapis.com"             # Cloud Build
    "cloudscheduler.googleapis.com"         # Cloud Scheduler
    "pubsub.googleapis.com"                 # Pub/Sub
    "monitoring.googleapis.com"             # Cloud Monitoring
    "logging.googleapis.com"                # Cloud Logging
    "cloudresourcemanager.googleapis.com"   # Resource Manager
    "iam.googleapis.com"                    # IAM
    "compute.googleapis.com"                # Compute (para Load Balancer)
    "artifactregistry.googleapis.com"       # Artifact Registry
)

# Habilitar servicios
for service in "${SERVICES[@]}"; do
    echo "Habilitando ${service}..."
    gcloud services enable "${service}" --project="${PROJECT_ID}" || true
done

echo ""
echo "✅ Servicios habilitados correctamente"
echo ""
echo "Servicios activos:"
gcloud services list --enabled --project="${PROJECT_ID}" --format="table(config.name)"

