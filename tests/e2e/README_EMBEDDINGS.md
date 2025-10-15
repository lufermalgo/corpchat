# Guía para Consultar y Probar Embeddings en BigQuery

Los embeddings de CorpChat se almacenan en BigQuery como vectores de 768 dimensiones.

## Schema de la Tabla

```
genai-385616.corpchat.embeddings

Campos:
- chunk_id: STRING (ID único del chunk)
- attachment_id: STRING (ID del documento)
- chat_id: STRING
- user_id: STRING  
- text: STRING (texto del chunk)
- embedding: FLOAT[] (vector de 768 dimensiones)
- page: INTEGER (número de página)
- source_filename: STRING
- chunk_index: INTEGER
- extraction_method: STRING (pdfplumber, ocr, etc.)
- created_at: TIMESTAMP
- expires_at: TIMESTAMP (TTL)
```

## Consultas Básicas

### 1. Ver todos los embeddings (sin el vector)

```bash
bq query --nouse_legacy_sql \
"SELECT 
  chunk_id,
  attachment_id,
  user_id,
  SUBSTR(text, 1, 100) as text_preview,
  chunk_index,
  page,
  source_filename,
  extraction_method,
  ARRAY_LENGTH(embedding) as dims,
  created_at
FROM \`genai-385616.corpchat.embeddings\`
ORDER BY created_at DESC
LIMIT 10"
```

### 2. Ver un embedding completo (con vector)

```bash
bq query --nouse_legacy_sql \
"SELECT 
  chunk_id,
  text,
  embedding,
  created_at
FROM \`genai-385616.corpchat.embeddings\`
LIMIT 1"
```

### 3. Estadísticas

```bash
bq query --nouse_legacy_sql \
"SELECT 
  COUNT(*) as total_chunks,
  COUNT(DISTINCT user_id) as users,
  COUNT(DISTINCT attachment_id) as documents,
  AVG(LENGTH(text)) as avg_text_length,
  MIN(created_at) as first,
  MAX(created_at) as last
FROM \`genai-385616.corpchat.embeddings\`"
```

### 4. Buscar por texto (LIKE)

```bash
bq query --nouse_legacy_sql \
"SELECT 
  chunk_id,
  text,
  attachment_id,
  page,
  created_at
FROM \`genai-385616.corpchat.embeddings\`
WHERE LOWER(text) LIKE '%corpchat%'
LIMIT 5"
```

## Búsqueda Semántica (Vector Search)

Para búsqueda vectorial necesitas:

### Opción 1: Script Bash (Simplificado)

```bash
./tests/e2e/query_embeddings.sh
```

Muestra estadísticas y listado de embeddings.

### Opción 2: Consola de BigQuery

1. Ir a https://console.cloud.google.com/bigquery?project=genai-385616
2. Ejecutar queries SQL directamente

### Opción 3: Python con Vector Search Completo

**Requisitos:**
```bash
pip install google-cloud-bigquery google-cloud-aiplatform
```

**Ejecutar:**
```bash
python3 tests/e2e/test_vector_search.py "¿Qué es CorpChat?"
```

**Cómo funciona:**
1. Genera embedding del query con Vertex AI
2. Calcula cosine similarity con todos los chunks:
   ```
   similarity = (A · B) / (||A|| * ||B||)
   ```
3. Retorna los top-K más similares

## Query SQL Completo para Vector Search

```sql
-- Ejemplo de búsqueda vectorial manual
-- (Reemplazar [QUERY_EMBEDDING] con vector real)

WITH query_embedding AS (
  SELECT [
    -0.015, 0.023, 0.041, ...  -- 768 valores
  ] AS vector
)

SELECT 
  e.chunk_id,
  e.text,
  e.attachment_id,
  
  -- Calcular cosine similarity
  (
    (SELECT SUM(a * b) 
     FROM UNNEST(e.embedding) AS a WITH OFFSET pos1
     JOIN UNNEST(q.vector) AS b WITH OFFSET pos2
     ON pos1 = pos2)
    /
    (
      SQRT((SELECT SUM(x * x) FROM UNNEST(e.embedding) AS x))
      *
      SQRT((SELECT SUM(y * y) FROM UNNEST(q.vector) AS y))
    )
  ) AS similarity_score,
  
  e.created_at

FROM `genai-385616.corpchat.embeddings` e
CROSS JOIN query_embedding q

WHERE (
  -- Calcular similarity (mismo cálculo de arriba)
  -- Solo incluir chunks con score >= 0.3
) >= 0.3

ORDER BY similarity_score DESC
LIMIT 5
```

## Ver Embeddings en la Consola

1. **BigQuery Console:**
   https://console.cloud.google.com/bigquery?project=genai-385616&p=genai-385616&d=corpchat&t=embeddings&page=table

2. **Cloud Run Logs (ver procesamiento):**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=corpchat-ingestor" --limit=50 --project=genai-385616
   ```

## Verificar el Pipeline Completo

### 1. Upload un documento de prueba

```bash
# Crear PDF de prueba
echo "CorpChat es una plataforma de chat empresarial con RAG." | \
  enscript -p /tmp/test.ps && \
  ps2pdf /tmp/test.ps /tmp/test.pdf

# Subir a GCS
gsutil cp /tmp/test.pdf \
  gs://corpchat-genai-385616-attachments/test/test.pdf

# Trigger procesamiento
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "gcs_path": "gs://corpchat-genai-385616-attachments/test/test.pdf",
    "attachment_id": "test-123",
    "chat_id": "chat-456",
    "user_id": "user-789",
    "mime_type": "application/pdf"
  }' \
  https://corpchat-ingestor-2s63drefva-uc.a.run.app/process
```

### 2. Verificar que se procesó

```bash
# Ver status del job
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://corpchat-ingestor-2s63drefva-uc.a.run.app/status/JOB_ID

# Verificar en BigQuery
bq query --nouse_legacy_sql \
"SELECT * FROM \`genai-385616.corpchat.embeddings\`
WHERE attachment_id = 'test-123'"
```

## Métricas de Vector Search

### Similitud coseno (Cosine Similarity)

- **1.0**: Idéntico (mismo vector)
- **0.9-1.0**: Extremadamente similar
- **0.7-0.9**: Muy similar (buen match para RAG)
- **0.5-0.7**: Moderadamente similar  
- **0.3-0.5**: Algo relacionado
- **< 0.3**: Poco relacionado

### Threshold recomendados

- **RAG production**: >= 0.7
- **Exploración**: >= 0.5
- **Testing**: >= 0.3

## Troubleshooting

### No hay embeddings

```bash
# Verificar tabla existe
bq show genai-385616:corpchat.embeddings

# Ver logs del ingestor
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=corpchat-ingestor AND severity>=WARNING" \
  --limit=20 --project=genai-385616
```

### Embeddings incorrectos

```bash
# Verificar dimensiones
bq query --nouse_legacy_sql \
"SELECT 
  chunk_id,
  ARRAY_LENGTH(embedding) as dims
FROM \`genai-385616.corpchat.embeddings\`
WHERE ARRAY_LENGTH(embedding) != 768"
```

Debería retornar 0 filas (todos deben tener 768 dims).

## Scripts Disponibles

- `query_embeddings.sh`: Ver y analizar embeddings
- `test_vector_search.py`: Búsqueda semántica completa (requiere deps)
- `test_vector_search_simple.sh`: Búsqueda simplificada sin deps
- `test_upload_process_query.sh`: Test E2E completo

## Ejemplo Completo

```bash
# 1. Ver qué hay en BigQuery
./tests/e2e/query_embeddings.sh

# 2. Hacer una búsqueda de texto
bq query --nouse_legacy_sql \
"SELECT text, attachment_id FROM \`genai-385616.corpchat.embeddings\`
WHERE LOWER(text) LIKE '%rag%'"

# 3. Test E2E completo (upload → process → verify)
./tests/e2e/test_upload_process_query.sh
```

---

**Última actualización**: 15 Octubre 2025

