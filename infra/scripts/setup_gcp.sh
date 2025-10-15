#!/bin/bash
set -euo pipefail

# Script de configuración completa de GCP para CorpChat MVP
# ⚠️  ADVERTENCIA: Este script crea recursos en un proyecto GCP COMPARTIDO
# ⚠️  Ejecutar ./audit_gcp.sh ANTES de usar este script

PROJECT_ID="${PROJECT_ID:-genai-385616}"
REGION="${REGION:-us-central1}"
GCS_BUCKET="${GCS_BUCKET:-corpchat-${PROJECT_ID}-attachments}"
SERVICE_ACCOUNT_NAME="corpchat-app"

# Parsear argumentos
DRY_RUN=false
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
    esac
done

echo "======================================"
echo "CorpChat MVP - Setup GCP"
echo "======================================"
echo "⚠️  PROYECTO COMPARTIDO: genai-385616"
echo "======================================"
echo "Proyecto: ${PROJECT_ID}"
echo "Región: ${REGION}"
echo "Bucket: ${GCS_BUCKET}"
echo "Service Account: ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if [[ "${DRY_RUN}" == "true" ]]; then
    echo ""
    echo "🔍 MODO DRY-RUN: Solo mostrará qué haría sin ejecutar"
fi

echo "======================================"
echo ""

# Verificar que se ejecutó audit_gcp.sh
echo "⚠️  IMPORTANTE: ¿Ejecutaste ./audit_gcp.sh y revisaste el reporte?"
echo "   Este proyecto está compartido con otros compañeros."
echo "   Crear recursos sin auditar puede romper proyectos existentes."
echo ""
read -p "¿Ejecutaste audit_gcp.sh y es seguro continuar? (yes/no): " -r AUDIT_CONFIRM
if [[ "$AUDIT_CONFIRM" != "yes" ]]; then
    echo "❌ Abortado. Ejecuta primero: ./audit_gcp.sh"
    exit 1
fi

echo ""
echo "Recursos que se crearán:"
echo "  ✓ Firestore (default) en ${REGION}"
echo "  ✓ Bucket GCS: gs://${GCS_BUCKET}"
echo "  ✓ Service Account: ${SERVICE_ACCOUNT_NAME}"
echo "  ✓ Pub/Sub Topic: attachments-finalized"
echo "  ✓ Secret: corpchat-config"
echo ""
echo "⚠️  Todos los recursos usan prefijo 'corpchat-' para evitar colisiones"
echo "⚠️  Firestore usará colecciones con prefijo 'corpchat_'"
echo ""
read -p "¿Continuar con la creación de recursos? (yes/no): " -r FINAL_CONFIRM
if [[ "$FINAL_CONFIRM" != "yes" ]]; then
    echo "❌ Abortado por el usuario"
    exit 0
fi

if [[ "${DRY_RUN}" == "true" ]]; then
    echo ""
    echo "✅ DRY-RUN completado. No se modificó nada."
    echo "   Para ejecutar realmente, quita el flag --dry-run"
    exit 0
fi

echo ""
echo "▶️  Iniciando configuración..."
echo ""

# 1. Configurar proyecto
echo "1️⃣  Configurando proyecto..."
gcloud config set project "${PROJECT_ID}"
gcloud config set run/region "${REGION}"

# 2. Habilitar servicios
echo ""
echo "2️⃣  Habilitando servicios GCP..."
./enable_services.sh

# 3. Crear Firestore en modo nativo
echo ""
echo "3️⃣  Creando Firestore en modo nativo..."
if gcloud firestore databases describe --format="value(name)" 2>/dev/null; then
    echo "   ℹ️  Firestore ya existe, omitiendo..."
else
    gcloud firestore databases create \
        --location="${REGION}" \
        --type=firestore-native \
        --project="${PROJECT_ID}"
    echo "   ✅ Firestore creado"
fi

# 4. Crear bucket GCS con lifecycle policies
echo ""
echo "4️⃣  Creando bucket GCS..."
if gsutil ls -b gs://"${GCS_BUCKET}" 2>/dev/null; then
    echo "   ℹ️  Bucket ya existe, omitiendo..."
else
    gsutil mb -l "${REGION}" gs://"${GCS_BUCKET}"
    
    # Aplicar lifecycle policy
    cat > /tmp/lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "SetStorageClass",
          "storageClass": "NEARLINE"
        },
        "condition": {
          "age": 30
        }
      },
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 180
        }
      }
    ]
  }
}
EOF
    
    gsutil lifecycle set /tmp/lifecycle.json gs://"${GCS_BUCKET}"
    rm /tmp/lifecycle.json
    
    # Habilitar uniform bucket-level access
    gsutil uniformbucketlevelaccess set on gs://"${GCS_BUCKET}"
    
    echo "   ✅ Bucket creado con lifecycle policies"
fi

# 5. Crear Service Account
echo ""
echo "5️⃣  Creando Service Account..."
SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" 2>/dev/null; then
    echo "   ℹ️  Service Account ya existe, omitiendo..."
else
    gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
        --display-name="CorpChat App Service Account" \
        --project="${PROJECT_ID}"
    echo "   ✅ Service Account creado: ${SA_EMAIL}"
fi

# 6. Asignar permisos al Service Account
echo ""
echo "6️⃣  Asignando permisos al Service Account..."

ROLES=(
    "roles/datastore.user"
    "roles/storage.objectAdmin"
    "roles/secretmanager.secretAccessor"
    "roles/aiplatform.user"
)

for role in "${ROLES[@]}"; do
    echo "   - Asignando ${role}..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="${role}" \
        --condition=None \
        --quiet
done

echo "   ✅ Permisos asignados"

# 7. Crear Pub/Sub topic para adjuntos
echo ""
echo "7️⃣  Creando Pub/Sub topic..."
TOPIC_NAME="attachments-finalized"

if gcloud pubsub topics describe "${TOPIC_NAME}" --project="${PROJECT_ID}" 2>/dev/null; then
    echo "   ℹ️  Topic ya existe, omitiendo..."
else
    gcloud pubsub topics create "${TOPIC_NAME}" --project="${PROJECT_ID}"
    echo "   ✅ Topic creado: ${TOPIC_NAME}"
fi

# 8. Configurar notificación de bucket a Pub/Sub
echo ""
echo "8️⃣  Configurando notificaciones GCS → Pub/Sub..."
gsutil notification create -t "${TOPIC_NAME}" -f json gs://"${GCS_BUCKET}" || true
echo "   ✅ Notificaciones configuradas"

# 9. Crear secret para configuración
echo ""
echo "9️⃣  Creando secret de configuración..."
SECRET_NAME="corpchat-config"

if gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" 2>/dev/null; then
    echo "   ℹ️  Secret ya existe, omitiendo..."
else
    gcloud secrets create "${SECRET_NAME}" \
        --replication-policy="automatic" \
        --project="${PROJECT_ID}"
    
    # Agregar primera versión con configuración básica
    echo -n "{\"BUCKET\":\"${GCS_BUCKET}\",\"REGION\":\"${REGION}\"}" | \
        gcloud secrets versions add "${SECRET_NAME}" --data-file=- --project="${PROJECT_ID}"
    
    echo "   ✅ Secret creado: ${SECRET_NAME}"
fi

# Resumen
echo ""
echo "======================================"
echo "✅ Setup completado exitosamente"
echo "======================================"
echo ""
echo "Recursos creados:"
echo "  - Proyecto: ${PROJECT_ID}"
echo "  - Región: ${REGION}"
echo "  - Firestore: (default) en ${REGION}"
echo "  - Bucket GCS: gs://${GCS_BUCKET}"
echo "  - Service Account: ${SA_EMAIL}"
echo "  - Pub/Sub Topic: ${TOPIC_NAME}"
echo "  - Secret: ${SECRET_NAME}"
echo ""
echo "Próximos pasos:"
echo "  1. Configurar IAP OAuth 2.0 Client ID en la consola de GCP"
echo "  2. Actualizar .env con las credenciales"
echo "  3. Desplegar servicios con Cloud Build"
echo ""

