#!/bin/bash
# Test E2E Básico: Upload PDF → Process → Query RAG
# Ejecutar desde el root del proyecto

set -e

PROJECT_ID="genai-385616"
REGION="us-central1"
BUCKET="corpchat-genai-385616-attachments"
BIGQUERY_DATASET="corpchat"
BIGQUERY_TABLE="embeddings"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "CorpChat - Test E2E Básico"
echo "======================================${NC}"
echo ""

# Variables de test
TEST_USER_ID="test-user-$(date +%s)"
TEST_CHAT_ID="test-chat-$(date +%s)"
TEST_ATTACHMENT_ID="test-attachment-$(date +%s)"
TEST_FILE="test_document.pdf"
TEST_CONTENT="CorpChat es una plataforma de chat corporativa con capacidades de RAG (Retrieval Augmented Generation). Permite a los usuarios consultar documentos empresariales de manera inteligente."

# URLs de servicios
INGESTOR_URL="https://corpchat-ingestor-2s63drefva-uc.a.run.app"
ORCHESTRATOR_URL="https://corpchat-orchestrator-2s63drefva-uc.a.run.app"

# Obtener token de autenticación
echo -e "${YELLOW}[1/6] Obteniendo token de autenticación...${NC}"
TOKEN=$(gcloud auth print-identity-token)
if [ -z "$TOKEN" ]; then
    echo -e "${RED}ERROR: No se pudo obtener el token de autenticación${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Token obtenido${NC}"
echo ""

# Crear PDF de prueba simple con texto
echo -e "${YELLOW}[2/6] Creando PDF de prueba...${NC}"

# Crear un archivo PS (PostScript) y convertirlo a PDF
cat > /tmp/${TEST_FILE%.pdf}.ps << 'PSEOF'
%!PS-Adobe-3.0
%%BoundingBox: 0 0 612 792
%%Title: CorpChat Test Document
%%Creator: CorpChat E2E Test
%%Pages: 1
%%EndComments

%%Page: 1 1
/Times-Roman findfont 12 scalefont setfont
72 720 moveto
(CorpChat es una plataforma de chat corporativa con capacidades) show
72 700 moveto
(de RAG \(Retrieval Augmented Generation\). Permite a los usuarios) show
72 680 moveto
(consultar documentos empresariales de manera inteligente.) show
showpage
%%EOF
PSEOF

# Convertir PS a PDF usando ps2pdf (incluido con ghostscript)
ps2pdf /tmp/${TEST_FILE%.pdf}.ps /tmp/${TEST_FILE} 2>&1 || {
    echo -e "${YELLOW}Warning: ps2pdf no disponible, usando alternativa...${NC}"
    # Alternativa: crear un PDF simple manualmente
    cat > /tmp/${TEST_FILE} << 'PDFEOF'
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Times-Roman
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
(CorpChat es una plataforma de chat corporativa con capacidades) Tj
0 -20 Td
(de RAG. Permite a los usuarios consultar documentos empresariales) Tj
0 -20 Td
(de manera inteligente.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
569
%%EOF
PDFEOF
}

if [ ! -f "/tmp/${TEST_FILE}" ]; then
    echo -e "${RED}ERROR: No se pudo crear el PDF${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PDF creado: /tmp/${TEST_FILE}${NC}"
echo ""

# Subir PDF a GCS
echo -e "${YELLOW}[3/6] Subiendo PDF a GCS...${NC}"
GCS_PATH="attachments/${TEST_USER_ID}/${TEST_CHAT_ID}/${TEST_ATTACHMENT_ID}/${TEST_FILE}"
gsutil cp /tmp/${TEST_FILE} gs://${BUCKET}/${GCS_PATH}

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: No se pudo subir el archivo a GCS${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Archivo subido a: gs://${BUCKET}/${GCS_PATH}${NC}"
echo ""

# Trigger procesamiento vía Ingestor
echo -e "${YELLOW}[4/6] Triggering procesamiento en Ingestor...${NC}"
PROCESS_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"gcs_path\": \"gs://${BUCKET}/${GCS_PATH}\",
    \"attachment_id\": \"${TEST_ATTACHMENT_ID}\",
    \"chat_id\": \"${TEST_CHAT_ID}\",
    \"user_id\": \"${TEST_USER_ID}\",
    \"mime_type\": \"application/pdf\"
  }" \
  ${INGESTOR_URL}/process)

echo "Response: $PROCESS_RESPONSE"

JOB_ID=$(echo $PROCESS_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null || echo "")

if [ -z "$JOB_ID" ]; then
    echo -e "${RED}ERROR: No se pudo obtener el job_id del procesamiento${NC}"
    echo "Response: $PROCESS_RESPONSE"
    exit 1
fi
echo -e "${GREEN}✓ Procesamiento iniciado. Job ID: ${JOB_ID}${NC}"
echo ""

# Esperar a que el procesamiento termine
echo -e "${YELLOW}[5/6] Esperando a que el procesamiento termine...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    sleep 5
    STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" ${INGESTOR_URL}/status/${JOB_ID})
    JOB_STATUS=$(echo $STATUS_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")
    
    echo -e "  Status: ${JOB_STATUS} (intento $((RETRY_COUNT+1))/${MAX_RETRIES})"
    
    if [ "$JOB_STATUS" = "completed" ]; then
        echo -e "${GREEN}✓ Procesamiento completado${NC}"
        break
    elif [ "$JOB_STATUS" = "failed" ]; then
        echo -e "${RED}ERROR: El procesamiento falló${NC}"
        echo "Response: $STATUS_RESPONSE"
        exit 1
    fi
    
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}ERROR: Timeout esperando el procesamiento${NC}"
    exit 1
fi
echo ""

# Verificar chunks en BigQuery
echo -e "${YELLOW}[6/6] Verificando chunks en BigQuery...${NC}"
QUERY="SELECT COUNT(*) as chunk_count 
FROM \`${PROJECT_ID}.${BIGQUERY_DATASET}.${BIGQUERY_TABLE}\` 
WHERE attachment_id = '${TEST_ATTACHMENT_ID}'"

CHUNK_COUNT=$(bq query --nouse_legacy_sql --format=csv "$QUERY" | tail -1)

echo -e "  Chunks encontrados: ${CHUNK_COUNT}"

if [ "$CHUNK_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Chunks almacenados en BigQuery${NC}"
else
    echo -e "${RED}ERROR: No se encontraron chunks en BigQuery${NC}"
    exit 1
fi
echo ""

# Query RAG desde Orchestrator
echo -e "${YELLOW}[BONUS] Query RAG desde Orchestrator...${NC}"
RAG_QUERY="¿Qué es CorpChat?"

RAG_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [{\"role\": \"user\", \"content\": \"${RAG_QUERY}\"}],
    \"user_id\": \"${TEST_USER_ID}\",
    \"chat_id\": \"${TEST_CHAT_ID}\"
  }" \
  ${ORCHESTRATOR_URL}/v1/chat/completions)

echo "RAG Response:"
echo "$RAG_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RAG_RESPONSE"
echo ""

# Cleanup
echo -e "${YELLOW}[CLEANUP] Limpiando archivos temporales...${NC}"
rm -f /tmp/${TEST_FILE}
rm -f /tmp/${TEST_FILE}.txt
echo -e "${GREEN}✓ Archivos temporales eliminados${NC}"
echo ""

# Resumen
echo -e "${BLUE}======================================"
echo "Resumen del Test E2E"
echo "======================================${NC}"
echo -e "Usuario: ${TEST_USER_ID}"
echo -e "Chat: ${TEST_CHAT_ID}"
echo -e "Attachment: ${TEST_ATTACHMENT_ID}"
echo -e "Job ID: ${JOB_ID}"
echo -e "Chunks almacenados: ${CHUNK_COUNT}"
echo -e "${GREEN}✅ TEST E2E EXITOSO${NC}"
echo ""

exit 0

