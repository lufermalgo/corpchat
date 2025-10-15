#!/bin/bash
set -euo pipefail

# Script de AUDITORÍA de GCP (SOLO LECTURA - NO MODIFICA NADA)
# Propósito: Revisar estado del proyecto genai-385616 ANTES de deployment

PROJECT_ID="${PROJECT_ID:-genai-385616}"
REGION="${REGION:-us-central1}"

echo "======================================"
echo "🔍 AUDITORÍA GCP - PROYECTO COMPARTIDO"
echo "======================================"
echo "Proyecto: ${PROJECT_ID}"
echo "Región: ${REGION}"
echo "⚠️  MODO: SOLO LECTURA (no modifica nada)"
echo "======================================"
echo ""

# Verificar autenticación
echo "1️⃣  Verificando autenticación..."
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "NO_AUTENTICADO")
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "NO_CONFIGURADO")

echo "   Cuenta actual: ${CURRENT_ACCOUNT}"
echo "   Proyecto configurado: ${CURRENT_PROJECT}"

if [[ "${CURRENT_PROJECT}" != "${PROJECT_ID}" ]]; then
    echo "   ⚠️  ADVERTENCIA: Proyecto configurado no coincide"
    echo "   Configurando proyecto correcto..."
    gcloud config set project "${PROJECT_ID}"
fi

echo ""

# Listar proyectos accesibles
echo "2️⃣  Listando proyectos accesibles..."
gcloud projects list --format="table(projectId,name,projectNumber)" | head -20
echo ""

# Verificar Firestore
echo "3️⃣  Verificando Firestore..."
if gcloud firestore databases list --format="value(name)" 2>/dev/null | grep -q .; then
    echo "   ✅ Firestore YA EXISTE"
    gcloud firestore databases list --format="table(name,type,locationId,createTime)"
    
    echo ""
    echo "   📊 Colecciones existentes (muestra):"
    # Intentar listar colecciones (requiere permisos)
    # Nota: Este comando puede fallar si no hay permisos
    gcloud firestore databases collections list --database="(default)" 2>/dev/null | head -10 || echo "   ℹ️  No se pueden listar colecciones (permisos insuficientes)"
else
    echo "   ℹ️  Firestore NO existe (se puede crear)"
fi

echo ""

# Verificar Cloud Run services
echo "4️⃣  Verificando Cloud Run services..."
RUN_SERVICES=$(gcloud run services list --region="${REGION}" --format="value(name)" 2>/dev/null | wc -l)
echo "   Servicios Cloud Run existentes: ${RUN_SERVICES}"

if [[ ${RUN_SERVICES} -gt 0 ]]; then
    echo ""
    echo "   📋 Servicios existentes:"
    gcloud run services list --region="${REGION}" --format="table(name,region,status,lastModified)" | head -20
    
    # Buscar servicios con prefijo "corpchat"
    echo ""
    echo "   🔍 Servicios con prefijo 'corpchat':"
    gcloud run services list --region="${REGION}" --format="value(name)" | grep "corpchat" || echo "   ✅ Ninguno (seguro para deployment)"
fi

echo ""

# Verificar Cloud Storage buckets
echo "5️⃣  Verificando Cloud Storage buckets..."
BUCKETS=$(gsutil ls 2>/dev/null | wc -l || echo "0")
echo "   Buckets existentes: ${BUCKETS}"

if [[ ${BUCKETS} -gt 0 ]]; then
    echo ""
    echo "   📋 Buckets (primeros 20):"
    gsutil ls | head -20
    
    # Buscar bucket específico
    echo ""
    echo "   🔍 Bucket 'corpchat-${PROJECT_ID}-attachments':"
    if gsutil ls "gs://corpchat-${PROJECT_ID}-attachments" 2>/dev/null; then
        echo "   ⚠️  YA EXISTE"
        echo "   Objetos en el bucket:"
        gsutil ls -l "gs://corpchat-${PROJECT_ID}-attachments/**" | head -10
    else
        echo "   ✅ NO existe (seguro para crear)"
    fi
fi

echo ""

# Verificar Service Accounts
echo "6️⃣  Verificando Service Accounts..."
SA_COUNT=$(gcloud iam service-accounts list --format="value(email)" 2>/dev/null | wc -l)
echo "   Service Accounts existentes: ${SA_COUNT}"

echo ""
echo "   🔍 Service Account 'corpchat-app':"
SA_EMAIL="corpchat-app@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe "${SA_EMAIL}" 2>/dev/null; then
    echo "   ⚠️  YA EXISTE"
else
    echo "   ✅ NO existe (seguro para crear)"
fi

echo ""

# Verificar Pub/Sub topics
echo "7️⃣  Verificando Pub/Sub topics..."
TOPICS=$(gcloud pubsub topics list --format="value(name)" 2>/dev/null | wc -l)
echo "   Topics existentes: ${TOPICS}"

if [[ ${TOPICS} -gt 0 ]]; then
    echo ""
    echo "   📋 Topics (primeros 20):"
    gcloud pubsub topics list --format="table(name)" | head -20
    
    echo ""
    echo "   🔍 Topic 'attachments-finalized':"
    if gcloud pubsub topics describe "attachments-finalized" 2>/dev/null; then
        echo "   ⚠️  YA EXISTE"
    else
        echo "   ✅ NO existe (seguro para crear)"
    fi
fi

echo ""

# Verificar Secrets
echo "8️⃣  Verificando Secret Manager..."
SECRETS=$(gcloud secrets list --format="value(name)" 2>/dev/null | wc -l)
echo "   Secrets existentes: ${SECRETS}"

if [[ ${SECRETS} -gt 0 ]]; then
    echo ""
    echo "   📋 Secrets (primeros 20):"
    gcloud secrets list --format="table(name,created)" | head -20
    
    echo ""
    echo "   🔍 Secret 'corpchat-config':"
    if gcloud secrets describe "corpchat-config" 2>/dev/null; then
        echo "   ⚠️  YA EXISTE"
    else
        echo "   ✅ NO existe (seguro para crear)"
    fi
fi

echo ""

# Verificar APIs habilitadas
echo "9️⃣  Verificando APIs habilitadas..."
echo "   APIs críticas para CorpChat:"

APIS=(
    "run.googleapis.com:Cloud Run"
    "firestore.googleapis.com:Firestore"
    "storage.googleapis.com:Cloud Storage"
    "aiplatform.googleapis.com:Vertex AI"
    "iap.googleapis.com:IAP"
    "secretmanager.googleapis.com:Secret Manager"
)

for api_info in "${APIS[@]}"; do
    IFS=':' read -r api_name api_label <<< "$api_info"
    if gcloud services list --enabled --filter="name:${api_name}" --format="value(name)" 2>/dev/null | grep -q "${api_name}"; then
        echo "   ✅ ${api_label}: HABILITADO"
    else
        echo "   ❌ ${api_label}: DESHABILITADO (se necesitará habilitar)"
    fi
done

echo ""

# Verificar Budgets
echo "🔟 Verificando Budgets..."
# Nota: Esto requiere billing.budgets.list permission
if gcloud billing budgets list --billing-account=ALL 2>/dev/null | grep -q .; then
    echo "   Budgets configurados (asociados a este proyecto):"
    gcloud billing budgets list --billing-account=ALL --format="table(displayName,amount,thresholdRules)" | head -10
else
    echo "   ℹ️  No se pueden listar budgets (permisos o no existen)"
fi

echo ""

# Resumen de riesgos
echo "======================================"
echo "📊 RESUMEN DE AUDITORÍA"
echo "======================================"
echo ""
echo "✅ RECURSOS QUE SE PUEDEN CREAR SEGUROS:"
echo "   (Aquellos que NO existen con prefijo 'corpchat')"
echo ""
echo "⚠️  RIESGOS POTENCIALES:"
echo ""

# Generar warnings basados en lo encontrado
WARNINGS=0

if gcloud run services list --region="${REGION}" --format="value(name)" 2>/dev/null | grep -q "corpchat"; then
    echo "   🚨 Cloud Run: Servicios 'corpchat' ya existen"
    ((WARNINGS++))
fi

if gsutil ls "gs://corpchat-${PROJECT_ID}-attachments" 2>/dev/null; then
    echo "   🚨 GCS: Bucket corpchat ya existe"
    ((WARNINGS++))
fi

if gcloud firestore databases list 2>/dev/null | grep -q .; then
    echo "   🚨 Firestore: Database ya existe (COMPARTIDA)"
    ((WARNINGS++))
fi

if [[ ${WARNINGS} -eq 0 ]]; then
    echo "   ✅ No se detectaron colisiones de nombres"
    echo "   ✅ Seguro para proceder con deployment"
else
    echo ""
    echo "   ⚠️  Se detectaron ${WARNINGS} posibles colisiones"
    echo "   ⚠️  REVISAR antes de ejecutar setup_gcp.sh"
fi

echo ""
echo "======================================"
echo "🔒 RECOMENDACIONES"
echo "======================================"
echo ""
echo "1. Si Firestore YA existe y es compartida:"
echo "   → Usar colecciones con prefijo: 'corpchat_users', 'corpchat_chats', etc."
echo "   → O considerar un proyecto GCP separado para CorpChat"
echo ""
echo "2. Si hay servicios Cloud Run existentes:"
echo "   → Verificar que no haya conflictos de nombres"
echo "   → Usar labels para identificar recursos: team=corpchat"
echo ""
echo "3. Antes de ejecutar setup_gcp.sh:"
echo "   → Revisar este reporte completo"
echo "   → Coordinar con el equipo si hay recursos compartidos"
echo "   → Considerar usar --dry-run en comandos de creación"
echo ""
echo "======================================"
echo "📝 Auditoría completada"
echo "Fecha: $(date)"
echo "======================================"

