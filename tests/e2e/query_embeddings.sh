#!/bin/bash
# Script para consultar y probar embeddings en BigQuery

PROJECT_ID="genai-385616"
DATASET="corpchat"
TABLE="embeddings"

echo "======================================"
echo "CorpChat - Query Embeddings en BigQuery"
echo "======================================"
echo ""

# 1. Ver todos los embeddings (sin el vector para que sea legible)
echo "[1] Lista de embeddings almacenados:"
echo "-----------------------------------"
bq query --nouse_legacy_sql --format=pretty \
"SELECT 
  chunk_id,
  attachment_id,
  chat_id,
  user_id,
  chunk_index,
  SUBSTR(text, 1, 100) as text_preview,
  page,
  source_filename,
  extraction_method,
  ARRAY_LENGTH(embedding) as embedding_dims,
  created_at
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
ORDER BY created_at DESC
LIMIT 10"

echo ""
echo ""

# 2. Ver un embedding completo (con el vector)
echo "[2] Ver un embedding completo (incluyendo vector):"
echo "-----------------------------------"
bq query --nouse_legacy_sql --format=pretty \
"SELECT 
  chunk_id,
  text,
  ARRAY_LENGTH(embedding) as dims,
  embedding[OFFSET(0)] as first_dim,
  embedding[OFFSET(767)] as last_dim,
  created_at
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
LIMIT 1"

echo ""
echo ""

# 3. Estadísticas de embeddings
echo "[3] Estadísticas de embeddings:"
echo "-----------------------------------"
bq query --nouse_legacy_sql --format=pretty \
"SELECT 
  COUNT(*) as total_embeddings,
  COUNT(DISTINCT user_id) as unique_users,
  COUNT(DISTINCT chat_id) as unique_chats,
  COUNT(DISTINCT attachment_id) as unique_attachments,
  MIN(created_at) as first_embedding,
  MAX(created_at) as last_embedding,
  AVG(LENGTH(text)) as avg_chunk_length
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`"

echo ""
echo ""

# 4. Embeddings por usuario
echo "[4] Embeddings por usuario:"
echo "-----------------------------------"
bq query --nouse_legacy_sql --format=pretty \
"SELECT 
  user_id,
  COUNT(*) as num_embeddings,
  COUNT(DISTINCT attachment_id) as num_documents,
  MAX(created_at) as last_upload
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
GROUP BY user_id
ORDER BY num_embeddings DESC"

echo ""

