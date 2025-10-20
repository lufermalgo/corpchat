#!/bin/bash
set -e

# Test E2E para Speech-to-Text (STT)
# Valida transcripción de audio usando Google Cloud Speech-to-Text

echo "🎤 CorpChat STT - E2E Tests"
echo "=========================="

# Configuración
GATEWAY_URL="https://corpchat-gateway-2s63drefva-uc.a.run.app"
TEST_LANGUAGES=("es" "en" "pt")
MIN_CONFIDENCE=0.8

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para crear audio de prueba
create_test_audio() {
    echo -e "${BLUE}🎵 Creando archivos de audio de prueba...${NC}"
    
    # Crear directorio de test si no existe
    mkdir -p test_audio
    
    # Crear audio de prueba con ffmpeg (si está disponible)
    if command -v ffmpeg &> /dev/null; then
        echo "Creando audio de prueba con ffmpeg..."
        
        # Audio en español
        ffmpeg -f lavfi -i "sine=frequency=1000:duration=3" -ar 16000 -ac 1 test_audio/spanish_test.wav 2>/dev/null || {
            echo -e "${YELLOW}⚠️ Error creando audio con ffmpeg${NC}"
            return 1
        }
        
        # Audio en inglés  
        ffmpeg -f lavfi -i "sine=frequency=800:duration=3" -ar 16000 -ac 1 test_audio/english_test.wav 2>/dev/null
        
        echo -e "${GREEN}✅ Archivos de audio creados${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ ffmpeg no disponible, usando archivos de texto como audio...${NC}"
        
        # Crear archivos de texto que simulen audio
        echo "Audio de prueba en español" > test_audio/spanish_test.wav
        echo "Test audio in English" > test_audio/english_test.wav
        
        echo -e "${GREEN}✅ Archivos de prueba creados${NC}"
        return 0
    fi
}

# Función para testear transcripción
test_transcription() {
    local audio_file=$1
    local language=$2
    local expected_language=$3
    
    echo -e "${BLUE}🧪 Probando transcripción $language -> $expected_language...${NC}"
    
    response=$(curl -s -X POST "$GATEWAY_URL/v1/audio/transcriptions" \
        -F "file=@$audio_file" \
        -F "model=whisper-1" \
        -F "language=$language" \
        -w "%{http_code}")
    
    http_code="${response: -3}"
    response_body="${response%???}"
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ Transcripción exitosa para $language${NC}"
        
        # Parsear respuesta JSON
        transcript=$(echo "$response_body" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('text', ''))
except:
    print('')
")
        
        language_detected=$(echo "$response_body" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('language', ''))
except:
    print('')
")
        
        if [ -n "$transcript" ]; then
            echo -e "${GREEN}✅ Transcripción obtenida: $transcript${NC}"
        else
            echo -e "${YELLOW}⚠️ Transcripción vacía${NC}"
        fi
        
        if [ "$language_detected" = "$expected_language" ]; then
            echo -e "${GREEN}✅ Idioma detectado correctamente: $language_detected${NC}"
        else
            echo -e "${YELLOW}⚠️ Idioma detectado: $language_detected (esperado: $expected_language)${NC}"
        fi
        
        return 0
    else
        echo -e "${RED}❌ Error en transcripción $language: HTTP $http_code${NC}"
        echo "Response: $response_body"
        return 1
    fi
}

# Función para verificar endpoints STT
test_stt_endpoints() {
    echo -e "${BLUE}🔍 Verificando endpoints STT...${NC}"
    
    # Test endpoint de modelos
    models_response=$(curl -s "$GATEWAY_URL/v1/audio/models")
    if echo "$models_response" | grep -q "whisper-1"; then
        echo -e "${GREEN}✅ Endpoint de modelos STT funcionando${NC}"
    else
        echo -e "${RED}❌ Error en endpoint de modelos${NC}"
        return 1
    fi
    
    # Test endpoint de idiomas
    languages_response=$(curl -s "$GATEWAY_URL/v1/audio/languages")
    if echo "$languages_response" | grep -q "es-ES"; then
        echo -e "${GREEN}✅ Endpoint de idiomas funcionando${NC}"
    else
        echo -e "${RED}❌ Error en endpoint de idiomas${NC}"
        return 1
    fi
    
    # Test endpoint de modelos STT específicos
    stt_models_response=$(curl -s "$GATEWAY_URL/v1/audio/models/stt")
    if echo "$stt_models_response" | grep -q "latest_long"; then
        echo -e "${GREEN}✅ Endpoint de modelos STT específicos funcionando${NC}"
    else
        echo -e "${RED}❌ Error en endpoint de modelos STT específicos${NC}"
        return 1
    fi
    
    return 0
}

# Función principal
main() {
    echo -e "${BLUE}🚀 Iniciando tests E2E de STT...${NC}"
    
    # Verificar dependencias
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}❌ curl no está instalado${NC}"
        exit 1
    fi
    
    # Crear archivos de audio de prueba
    if ! create_test_audio; then
        echo -e "${RED}❌ Error creando archivos de audio${NC}"
        exit 1
    fi
    
    # Tests por endpoint
    tests_passed=0
    tests_total=0
    
    # Test 1: Endpoints STT
    tests_total=$((tests_total + 1))
    if test_stt_endpoints; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 2: Transcripción español
    tests_total=$((tests_total + 1))
    if test_transcription "test_audio/spanish_test.wav" "es" "es-ES"; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 3: Transcripción inglés
    tests_total=$((tests_total + 1))
    if test_transcription "test_audio/english_test.wav" "en" "en-US"; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Resumen final
    echo ""
    echo "=========================="
    echo -e "${BLUE}📋 RESUMEN DE TESTS DE STT${NC}"
    echo "=========================="
    echo -e "✅ Tests pasados: $tests_passed/$tests_total"
    
    if [ $tests_passed -eq $tests_total ]; then
        echo -e "${GREEN}🎉 ¡Todos los tests de STT pasaron!${NC}"
        echo ""
        echo -e "${BLUE}📋 PRÓXIMOS PASOS:${NC}"
        echo "1. Probar STT desde Open WebUI interface"
        echo "2. Validar transcripción con audio real"
        echo "3. Probar diferentes idiomas y acentos"
        echo "4. Monitorear métricas de precisión"
        
        # Limpiar archivos de prueba
        echo ""
        echo -e "${BLUE}🧹 Limpiando archivos de prueba...${NC}"
        rm -rf test_audio
        echo -e "${GREEN}✅ Limpieza completada${NC}"
        
        exit 0
    else
        echo -e "${RED}❌ $((tests_total - tests_passed)) tests fallaron${NC}"
        echo ""
        echo -e "${BLUE}🔧 ACCIONES RECOMENDADAS:${NC}"
        echo "1. Revisar logs del servicio Gateway"
        echo "2. Verificar permisos de Speech-to-Text API"
        echo "3. Validar configuración de Open WebUI"
        echo "4. Comprobar conectividad de servicios"
        
        exit 1
    fi
}

# Ejecutar tests
main "$@"
