#!/bin/bash
set -euo pipefail

# Script de configuración de BigQuery Vector Store para CorpChat
# Proyecto: genai-385616

PROJECT_ID="${PROJECT_ID:-genai-385616}"
DATASET="corpchat"
TABLE="embeddings"
REGION="${REGION:-us-central1}"

echo "======================================"
echo "BigQuery Vector Store Setup"
echo "======================================"
echo "Proyecto: ${PROJECT_ID}"
echo "Dataset: ${DATASET}"
echo "Tabla: ${TABLE}"
echo "Región: ${REGION}"
echo "======================================"
echo ""

# 1. Crear dataset si no existe
echo "1️⃣  Creando dataset BigQuery..."
bq mk --dataset \
  --location="${REGION}" \
  --description="CorpChat vector embeddings store" \
  "${PROJECT_ID}:${DATASET}" 2>/dev/null || echo "   ℹ️  Dataset ya existe"

# 2. Crear tabla de embeddings
echo ""
echo "2️⃣  Creando tabla de embeddings..."

# Crear schema file temporal
cat > /tmp/bq_embeddings_schema.json <<EOF
[
  {"name": "chunk_id", "type": "STRING", "mode": "REQUIRED", "description": "ID único del chunk"},
  {"name": "attachment_id", "type": "STRING", "mode": "REQUIRED", "description": "ID del documento adjunto"},
  {"name": "chat_id", "type": "STRING", "mode": "REQUIRED", "description": "ID del chat"},
  {"name": "user_id", "type": "STRING", "mode": "REQUIRED", "description": "ID del usuario"},
  {"name": "text", "type": "STRING", "mode": "REQUIRED", "description": "Texto del chunk"},
  {"name": "embedding", "type": "FLOAT64", "mode": "REPEATED", "description": "Vector embedding (768 dims)"},
  {"name": "page", "type": "INT64", "mode": "NULLABLE", "description": "Número de página (si aplica)"},
  {"name": "source_filename", "type": "STRING", "mode": "NULLABLE", "description": "Nombre del archivo fuente"},
  {"name": "chunk_index", "type": "INT64", "mode": "NULLABLE", "description": "Índice del chunk en el documento"},
  {"name": "extraction_method", "type": "STRING", "mode": "NULLABLE", "description": "Método de extracción (text, ocr, table)"},
  {"name": "created_at", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Timestamp de creación"},
  {"name": "expires_at", "type": "TIMESTAMP", "mode": "NULLABLE", "description": "Timestamp de expiración (TTL)"}
]
EOF

# Crear tabla con particionamiento y clustering
bq mk --table \
  --time_partitioning_field created_at \
  --time_partitioning_type DAY \
  --time_partitioning_expiration 2592000 \
  --clustering_fields user_id,chat_id \
  --description="Embeddings vectoriales para búsqueda semántica" \
  "${PROJECT_ID}:${DATASET}.${TABLE}" \
  /tmp/bq_embeddings_schema.json 2>/dev/null || echo "   ℹ️  Tabla ya existe"

rm /tmp/bq_embeddings_schema.json

# 3. Verificar tabla creada
echo ""
echo "3️⃣  Verificando configuración de la tabla..."
bq show "${PROJECT_ID}:${DATASET}.${TABLE}"

# 4. Asignar permisos al service account
echo ""
echo "4️⃣  Asignando permisos BigQuery al service account..."
SA_EMAIL="corpchat-app@${PROJECT_ID}.iam.gserviceaccount.com"

# BigQuery Data Editor (para inserts)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.dataEditor" \
  --condition=None \
  --quiet

# BigQuery Job User (para queries)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.jobUser" \
  --condition=None \
  --quiet

echo "   ✅ Permisos asignados"

# 5. Crear view para debugging (opcional)
echo ""
echo "5️⃣  Creando view de debugging..."
bq mk --view \
  "SELECT 
    chunk_id, 
    chat_id, 
    user_id, 
    LEFT(text, 100) as text_preview,
    ARRAY_LENGTH(embedding) as embedding_dims,
    source_filename,
    page,
    created_at,
    expires_at
  FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
  WHERE expires_at > CURRENT_TIMESTAMP() OR expires_at IS NULL
  ORDER BY created_at DESC
  LIMIT 100" \
  "${PROJECT_ID}:${DATASET}.embeddings_view" 2>/dev/null || echo "   ℹ️  View ya existe"

echo ""
echo "======================================"
echo "✅ BigQuery Vector Store configurado"
echo "======================================"
echo ""
echo "Recursos creados:"
echo "  - Dataset: ${PROJECT_ID}:${DATASET}"
echo "  - Tabla: ${TABLE}"
echo "  - View: embeddings_view"
echo ""
echo "Configuración:"
echo "  - Particionamiento: Diario por created_at"
echo "  - Expiración particiones: 30 días"
echo "  - Clustering: user_id, chat_id"
echo "  - Permisos: corpchat-app SA"
echo ""
echo "Queries de ejemplo:"
echo ""
echo "  # Contar chunks"
echo "  bq query --nouse_legacy_sql \\"
echo "    'SELECT COUNT(*) as total FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`'"
echo ""
echo "  # Ver últimos chunks"
echo "  bq query --nouse_legacy_sql \\"
echo "    'SELECT * FROM \`${PROJECT_ID}.${DATASET}.embeddings_view\` LIMIT 10'"
echo ""
echo "  # Buscar por chat"
echo "  bq query --nouse_legacy_sql \\"
echo "    'SELECT chunk_id, text FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\` WHERE chat_id=\"xxx\" LIMIT 5'"
echo ""

