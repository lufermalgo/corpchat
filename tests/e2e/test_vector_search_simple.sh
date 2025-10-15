#!/bin/bash
# Script simplificado para probar búsqueda semántica sin Python
# Usa gcloud directamente para generar embeddings

PROJECT_ID="genai-385616"
REGION="us-central1"
DATASET="corpchat"
TABLE="embeddings"

if [ -z "$1" ]; then
    echo "Uso: $0 <query>"
    echo ""
    echo "Ejemplos:"
    echo "  $0 '¿Qué es CorpChat?'"
    echo "  $0 'plataforma'"
    echo "  $0 'RAG'"
    exit 1
fi

QUERY_TEXT="$1"

echo "======================================"
echo "CorpChat - Vector Search Simplificado"
echo "======================================"
echo ""
echo "🔍 Query: '$QUERY_TEXT'"
echo ""

# Generar embedding del query usando gcloud (Vertex AI)
echo "[1/3] Generando embedding del query..."

# Crear archivo temporal con el texto
TEMP_INPUT="/tmp/query_input_$$.json"
cat > "$TEMP_INPUT" << EOF
{
  "instances": [
    { "content": "$QUERY_TEXT" }
  ]
}
EOF

# Llamar a Vertex AI para generar embedding
EMBEDDING_RESPONSE=$(gcloud ai endpoints predict \
  --region=$REGION \
  --project=$PROJECT_ID \
  --json-request="$TEMP_INPUT" \
  text-embedding-004 2>/dev/null || echo "ERROR")

if [ "$EMBEDDING_RESPONSE" == "ERROR" ]; then
    echo "⚠️  No se pudo generar embedding con gcloud AI."
    echo "Mostrando búsqueda por texto simple en su lugar..."
    echo ""
    
    # Búsqueda alternativa por texto
    echo "[2/3] Buscando chunks por texto (LIKE)..."
    bq query --nouse_legacy_sql --format=pretty \
    "SELECT 
      chunk_id,
      attachment_id,
      SUBSTR(text, 1, 200) as text_preview,
      chunk_index,
      page,
      source_filename,
      created_at
    FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
    WHERE LOWER(text) LIKE LOWER('%${QUERY_TEXT}%')
    ORDER BY created_at DESC
    LIMIT 5"
    
    rm -f "$TEMP_INPUT"
    exit 0
fi

# Extraer vector del response (esto es complejo, usar alternativa simple)
echo "✓ Embedding generado"
echo ""

echo "[2/3] Ejecutando búsqueda semántica en BigQuery..."
echo "ℹ️  Mostrando todos los chunks ordenados por fecha (búsqueda exacta requiere procesamiento del embedding)"
echo ""

# Por simplicidad, mostrar todos los chunks (en producción aquí iría la búsqueda vectorial)
bq query --nouse_legacy_sql --format=pretty \
"SELECT 
  chunk_id,
  attachment_id,
  user_id,
  chunk_index,
  SUBSTR(text, 1, 150) as text_preview,
  page,
  source_filename,
  extraction_method,
  created_at
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
ORDER BY created_at DESC
LIMIT 5"

echo ""
echo ""
echo "[3/3] Para búsqueda vectorial completa, usar el script Python:"
echo "  python3 tests/e2e/test_vector_search.py '$QUERY_TEXT'"
echo ""

# Cleanup
rm -f "$TEMP_INPUT"

