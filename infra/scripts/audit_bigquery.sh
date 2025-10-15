#!/bin/bash
set -euo pipefail

# Script de AUDITORÍA de BigQuery (SOLO LECTURA - NO MODIFICA NADA)
# Propósito: Revisar datasets y tablas existentes ANTES de crear recursos

PROJECT_ID="${PROJECT_ID:-genai-385616}"
DATASET="corpchat"
TABLE="embeddings"

echo "======================================"
echo "🔍 AUDITORÍA BIGQUERY - PROYECTO COMPARTIDO"
echo "======================================"
echo "Proyecto: ${PROJECT_ID}"
echo "Dataset objetivo: ${DATASET}"
echo "Tabla objetivo: ${TABLE}"
echo "⚠️  MODO: SOLO LECTURA (no modifica nada)"
echo "======================================"
echo ""

# Verificar autenticación
echo "1️⃣  Verificando autenticación BigQuery..."
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "NO_CONFIGURADO")
echo "   Proyecto configurado: ${CURRENT_PROJECT}"

if [[ "${CURRENT_PROJECT}" != "${PROJECT_ID}" ]]; then
    echo "   ⚠️  ADVERTENCIA: Proyecto configurado no coincide"
    gcloud config set project "${PROJECT_ID}"
fi

echo ""

# Listar TODOS los datasets
echo "2️⃣  Listando datasets existentes en ${PROJECT_ID}..."
DATASETS=$(bq ls --format=prettyjson --max_results=1000 2>/dev/null | jq -r '.[].datasetReference.datasetId' | wc -l || echo "0")
echo "   Datasets existentes: ${DATASETS}"

if [[ ${DATASETS} -gt 0 ]]; then
    echo ""
    echo "   📋 Datasets (primeros 50):"
    bq ls --max_results=50 | head -50
    
    echo ""
    echo "   🔍 Buscando datasets con prefijo 'corpchat':"
    bq ls --max_results=1000 | grep -i "corpchat" || echo "   ✅ Ninguno encontrado (seguro para crear)"
fi

echo ""

# Verificar si existe el dataset "corpchat"
echo "3️⃣  Verificando dataset '${DATASET}'..."
if bq ls --dataset "${PROJECT_ID}:${DATASET}" 2>/dev/null | grep -q "${DATASET}"; then
    echo "   ⚠️  Dataset '${DATASET}' YA EXISTE"
    
    # Mostrar info del dataset
    echo ""
    echo "   📊 Información del dataset:"
    bq show --format=prettyjson "${PROJECT_ID}:${DATASET}" | jq '{
      id: .id,
      location: .location,
      created: .creationTime,
      modified: .lastModifiedTime,
      labels: .labels
    }'
    
    # Listar tablas en el dataset
    echo ""
    echo "   📋 Tablas en el dataset '${DATASET}':"
    TABLES=$(bq ls "${PROJECT_ID}:${DATASET}" 2>/dev/null | tail -n +3 | wc -l || echo "0")
    echo "   Tablas existentes: ${TABLES}"
    
    if [[ ${TABLES} -gt 0 ]]; then
        bq ls "${PROJECT_ID}:${DATASET}"
        
        # Verificar si existe la tabla "embeddings"
        echo ""
        echo "   🔍 Verificando tabla '${TABLE}':"
        if bq show --format=prettyjson "${PROJECT_ID}:${DATASET}.${TABLE}" 2>/dev/null; then
            echo "   🚨 TABLA '${TABLE}' YA EXISTE"
            
            echo ""
            echo "   📊 Schema de la tabla existente:"
            bq show --schema --format=prettyjson "${PROJECT_ID}:${DATASET}.${TABLE}" | jq '.[] | {name: .name, type: .type, mode: .mode}'
            
            echo ""
            echo "   📊 Estadísticas de la tabla:"
            bq show --format=prettyjson "${PROJECT_ID}:${DATASET}.${TABLE}" | jq '{
              numRows: .numRows,
              numBytes: .numBytes,
              creationTime: .creationTime,
              lastModifiedTime: .lastModifiedTime,
              type: .type,
              location: .location
            }'
            
            echo ""
            echo "   ⚠️  ADVERTENCIA: NO CREAR NI MODIFICAR ESTA TABLA"
        else
            echo "   ✅ Tabla '${TABLE}' NO existe (seguro para crear)"
        fi
    fi
else
    echo "   ✅ Dataset '${DATASET}' NO existe (seguro para crear)"
fi

echo ""

# Buscar tablas relacionadas con embeddings en TODOS los datasets
echo "4️⃣  Buscando tablas relacionadas con 'embedding' en todos los datasets..."
echo "   (Esto puede tomar unos segundos...)"
echo ""

FOUND_EMBEDDINGS=false
for dataset in $(bq ls --format=csv --max_results=1000 | tail -n +2 | cut -d',' -f1); do
    TABLES_WITH_EMBEDDING=$(bq ls --format=csv "${PROJECT_ID}:${dataset}" 2>/dev/null | tail -n +2 | grep -i "embedding" || true)
    
    if [[ -n "${TABLES_WITH_EMBEDDING}" ]]; then
        echo "   📋 Dataset: ${dataset}"
        echo "${TABLES_WITH_EMBEDDING}" | while read -r table; do
            echo "      - ${table}"
        done
        FOUND_EMBEDDINGS=true
    fi
done

if [[ "${FOUND_EMBEDDINGS}" == "false" ]]; then
    echo "   ✅ No se encontraron tablas con 'embedding' en el nombre"
fi

echo ""

# Verificar permisos del service account
echo "5️⃣  Verificando permisos del service account..."
SA_EMAIL="corpchat-app@${PROJECT_ID}.iam.gserviceaccount.com"

echo "   Service Account: ${SA_EMAIL}"
echo ""
echo "   Roles de BigQuery asignados:"

# Buscar roles de BigQuery
BQ_ROLES=$(gcloud projects get-iam-policy "${PROJECT_ID}" \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:${SA_EMAIL}" \
    --format="value(bindings.role)" 2>/dev/null | grep bigquery || echo "   ℹ️  Sin roles de BigQuery asignados")

if [[ -n "${BQ_ROLES}" ]]; then
    echo "${BQ_ROLES}"
else
    echo "   ⚠️  Service Account NO tiene roles de BigQuery"
    echo "   Roles necesarios:"
    echo "      - roles/bigquery.dataEditor (para inserts/updates)"
    echo "      - roles/bigquery.jobUser (para queries)"
fi

echo ""

# Estimar costos de storage si existen datos
echo "6️⃣  Estimando costos de BigQuery storage..."
TOTAL_BYTES=$(bq ls --format=json --max_results=1000 2>/dev/null | \
    jq '[.[] | select(.datasetReference.datasetId != null)] | 
        map(select(.id != null)) | 
        length' 2>/dev/null || echo "0")

if [[ ${TOTAL_BYTES} -gt 0 ]]; then
    echo "   Total datasets con datos: ${TOTAL_BYTES}"
    echo "   ℹ️  Para costo detallado, revisar Cloud Billing"
else
    echo "   ℹ️  No se pudo calcular uso de storage"
fi

echo ""

# Verificar quotas de BigQuery
echo "7️⃣  Verificando quotas de BigQuery..."
echo "   Consultando límites del proyecto..."
echo ""

# Queries por día (no hay comando directo, mostrar info general)
echo "   ℹ️  Quotas de BigQuery por proyecto:"
echo "      - Queries por día: 2,000 (default, puede ser mayor)"
echo "      - Bytes escaneados por día: Sin límite por defecto"
echo "      - Slots concurrentes: 2,000 (on-demand)"
echo "      - Jobs concurrentes: 50-100"
echo ""
echo "   Para verificar uso actual:"
echo "   → https://console.cloud.google.com/bigquery/admin/quotas?project=${PROJECT_ID}"

echo ""

# Resumen de riesgos
echo "======================================"
echo "📊 RESUMEN DE AUDITORÍA BIGQUERY"
echo "======================================"
echo ""

WARNINGS=0

if bq ls --dataset "${PROJECT_ID}:${DATASET}" 2>/dev/null | grep -q "${DATASET}"; then
    echo "   🚨 Dataset '${DATASET}' ya existe"
    ((WARNINGS++))
    
    if bq show "${PROJECT_ID}:${DATASET}.${TABLE}" 2>/dev/null | grep -q "tableReference"; then
        echo "   🚨 Tabla '${TABLE}' ya existe en dataset '${DATASET}'"
        ((WARNINGS++))
    fi
fi

if [[ ${WARNINGS} -eq 0 ]]; then
    echo "   ✅ No se detectaron colisiones"
    echo "   ✅ Seguro para crear dataset '${DATASET}' y tabla '${TABLE}'"
else
    echo ""
    echo "   ⚠️  Se detectaron ${WARNINGS} posibles colisiones"
    echo "   ⚠️  REVISAR antes de ejecutar setup_bigquery_vector_store.sh"
    echo ""
    echo "   Opciones:"
    echo "   1. Usar un nombre diferente para el dataset (ej: corpchat_dev)"
    echo "   2. Usar un nombre diferente para la tabla (ej: embeddings_v2)"
    echo "   3. Verificar si los recursos existentes son de otro proyecto"
    echo "   4. Coordinar con el equipo propietario de los recursos"
fi

echo ""
echo "======================================"
echo "🔒 RECOMENDACIONES"
echo "======================================"
echo ""
echo "1. Si el dataset '${DATASET}' ya existe:"
echo "   → Verificar quién lo creó y para qué"
echo "   → Considerar sufijo: corpchat_mvp, corpchat_dev, etc."
echo "   → NO modificar tablas existentes"
echo ""
echo "2. Antes de ejecutar setup_bigquery_vector_store.sh:"
echo "   → Revisar este reporte completo"
echo "   → Coordinar con el equipo si hay recursos compartidos"
echo "   → Asegurar que service account tiene permisos"
echo ""
echo "3. Naming convention sugerida:"
echo "   → Dataset: corpchat (o corpchat_ENV si hay conflicto)"
echo "   → Tabla: embeddings"
echo "   → Views: embeddings_view, embeddings_stats"
echo ""
echo "======================================"
echo "📝 Auditoría completada"
echo "Fecha: $(date)"
echo "======================================"

