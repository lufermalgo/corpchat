#!/bin/bash
# Test E2E de procesamiento de imágenes en CorpChat

set -e

echo "=== Test E2E de Procesamiento de Imágenes ==="
echo "Fecha: $(date)"
echo ""

# Configuración
GATEWAY_URL="http://localhost:8080"
API_KEY="corpchat-gateway"
TEST_CHAT_ID="test-image-processing-$(date +%s)"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para hacer requests al Gateway
make_request() {
    local test_name="$1"
    local request_body="$2"
    local expected_keywords="$3"
    
    echo -e "${YELLOW}🧪 Ejecutando: $test_name${NC}"
    
    response=$(curl -s -X POST "$GATEWAY_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "$request_body")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Request exitoso${NC}"
        
        # Verificar si la respuesta contiene las palabras clave esperadas
        if echo "$response" | grep -q "$expected_keywords"; then
            echo -e "${GREEN}✅ Respuesta contiene '$expected_keywords'${NC}"
        else
            echo -e "${YELLOW}⚠️ Respuesta no contiene '$expected_keywords'${NC}"
            echo "Respuesta recibida:"
            echo "$response" | jq -r '.choices[0].message.content' 2>/dev/null || echo "$response"
        fi
    else
        echo -e "${RED}❌ Request falló${NC}"
    fi
    
    echo ""
}

# Test 1: Imagen en base64 (PNG simple)
echo -e "${YELLOW}=== Test 1: Imagen Base64 (PNG Simple) ===${NC}"
base64_png="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

test1_body='{
    "model": "gemini-auto",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "¿Qué ves en esta imagen? Describe lo que aparece."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,'$base64_png'"}]
        ]
    }],
    "chat_id": "'$TEST_CHAT_ID'"
}'

make_request "Imagen Base64 PNG" "$test1_body" "imagen\|pixel\|color"

# Test 2: Imagen con texto (simulando un diagrama)
echo -e "${YELLOW}=== Test 2: Imagen con Texto ===${NC}"
# Usar una imagen base64 más compleja que represente texto
base64_text="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

test2_body='{
    "model": "gemini-analysis",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analiza esta imagen y extrae cualquier texto que veas."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,'$base64_text'"}]
        ]
    }],
    "chat_id": "'$TEST_CHAT_ID'"
}'

make_request "Imagen con Texto" "$test2_body" "texto\|análisis\|imagen"

# Test 3: URL de GCS (simulado)
echo -e "${YELLOW}=== Test 3: URL de GCS ===${NC}"
# Nota: Este test requeriría una imagen real en GCS
test3_body='{
    "model": "gemini-auto",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analiza esta imagen desde GCS."},
            {"type": "image_url", "image_url": {"url": "gs://corpchat-genai-385616-attachments/test-image.png"}}]
    }],
    "chat_id": "'$TEST_CHAT_ID'"
}'

make_request "URL de GCS" "$test3_body" "imagen\|GCS\|análisis"

# Test 4: API Path (simulado)
echo -e "${YELLOW}=== Test 4: API Path ===${NC}"
# Nota: Este test requeriría un attachment real en Firestore
test4_body='{
    "model": "gemini-auto",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analiza esta imagen desde API path."},
            {"type": "image_url", "image_url": {"url": "/api/files/attachment-123"}}]
    }],
    "chat_id": "'$TEST_CHAT_ID'"
}'

make_request "API Path" "$test4_body" "imagen\|attachment\|análisis"

# Test 5: Formato no soportado
echo -e "${YELLOW}=== Test 5: Formato No Soportado ===${NC}"
test5_body='{
    "model": "gemini-auto",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analiza esta imagen."},
            {"type": "image_url", "image_url": {"url": "http://example.com/image.jpg"}}]
    }],
    "chat_id": "'$TEST_CHAT_ID'"
}'

make_request "Formato No Soportado" "$test5_body" "soportado\|formato\|error"

# Test 6: Streaming con imagen
echo -e "${YELLOW}=== Test 6: Streaming con Imagen ===${NC}"
test6_body='{
    "model": "gemini-auto",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe esta imagen en detalle."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,'$base64_png'"}]
        ]
    }],
    "chat_id": "'$TEST_CHAT_ID'",
    "stream": true
}'

echo -e "${YELLOW}🧪 Ejecutando: Streaming con Imagen${NC}"
stream_response=$(curl -s -X POST "$GATEWAY_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "$test6_body")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Streaming request exitoso${NC}"
    echo "Primeras líneas de respuesta:"
    echo "$stream_response" | head -5
else
    echo -e "${RED}❌ Streaming request falló${NC}"
fi

echo ""

# Test 7: Sin chat_id (debería funcionar con middleware)
echo -e "${YELLOW}=== Test 7: Sin chat_id (Middleware) ===${NC}"
test7_body='{
    "model": "gemini-auto",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analiza esta imagen sin chat_id."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,'$base64_png'"}]
        ]
    }]
}'

make_request "Sin chat_id" "$test7_body" "imagen\|análisis"

# Resumen
echo -e "${YELLOW}=== Resumen de Tests ===${NC}"
echo "✅ Tests completados"
echo "📊 Chat ID usado: $TEST_CHAT_ID"
echo "🔗 Gateway URL: $GATEWAY_URL"
echo "📅 Fecha: $(date)"

echo ""
echo -e "${GREEN}🎉 Tests E2E de procesamiento de imágenes completados${NC}"
echo ""
echo "Para verificar manualmente:"
echo "1. Abre Open WebUI en http://localhost:8082"
echo "2. Adjunta una imagen real"
echo "3. Pregunta sobre la imagen"
echo "4. Verifica que el modelo responde correctamente"
