#!/bin/bash

# Script para ejecutar tests E2E en desarrollo local de CorpChat
# Valida que todos los servicios funcionen correctamente

echo "🧪 EJECUTANDO TESTS E2E PARA DESARROLLO LOCAL"
echo "============================================="
echo ""

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Función para incrementar contadores
increment_test() {
    ((TESTS_TOTAL++))
    if [ $1 -eq 0 ]; then
        ((TESTS_PASSED++))
        echo -e "${GREEN}✅ PASS${NC}"
    else
        ((TESTS_FAILED++))
        echo -e "${RED}❌ FAIL${NC}"
    fi
}

# Función para verificar que los servicios estén corriendo
check_services_running() {
    echo -e "${BLUE}🔍 Verificando servicios en ejecución...${NC}"
    
    cd "$PROJECT_ROOT"
    
    local services=("corpchat-gateway" "corpchat-ingestor" "corpchat-ui")
    local all_running=true
    
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            echo -e "  ✅ $service está corriendo"
        else
            echo -e "  ❌ $service NO está corriendo"
            all_running=false
        fi
    done
    
    if [ "$all_running" = true ]; then
        echo -e "${GREEN}✅ Todos los servicios están corriendo${NC}"
        return 0
    else
        echo -e "${RED}❌ Algunos servicios no están corriendo${NC}"
        return 1
    fi
}

# Función para test de conectividad básica
test_basic_connectivity() {
    echo ""
    echo -e "${BLUE}🌐 Test: Conectividad básica${NC}"
    
    local endpoints=(
        "http://localhost:8080/health:Gateway Health"
        "http://localhost:8081/health:Ingestor Health"
        "http://localhost:8082/health:UI Health"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        local url=$(echo "$endpoint_info" | cut -d':' -f1-3)
        local name=$(echo "$endpoint_info" | cut -d':' -f4)
        
        echo -n "  Testing $name ($url)... "
        
        if curl -f -s "$url" >/dev/null 2>&1; then
            increment_test 0
        else
            increment_test 1
        fi
    done
}

# Función para test de modelos disponibles
test_models_endpoint() {
    echo ""
    echo -e "${BLUE}🤖 Test: Endpoint de modelos${NC}"
    
    echo -n "  Testing /v1/models endpoint... "
    
    local response=$(curl -s "http://localhost:8080/v1/models" 2>/dev/null)
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8080/v1/models" 2>/dev/null)
    
    if [ "$status_code" = "200" ] && echo "$response" | grep -q "gemini"; then
        increment_test 0
        echo "  📊 Modelos encontrados: $(echo "$response" | jq -r '.data[].id' 2>/dev/null | wc -l)"
    else
        increment_test 1
        echo "  📊 Status: $status_code"
    fi
}

# Función para test de chat completions
test_chat_completions() {
    echo ""
    echo -e "${BLUE}💬 Test: Chat completions${NC}"
    
    echo -n "  Testing /v1/chat/completions endpoint... "
    
    local test_payload='{
        "model": "gemini-2.5-flash-001",
        "messages": [{"role": "user", "content": "Hola, ¿puedes responder con un simple saludo?"}],
        "max_tokens": 50
    }'
    
    local response=$(curl -s -X POST "http://localhost:8080/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "$test_payload" 2>/dev/null)
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8080/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "$test_payload" 2>/dev/null)
    
    if [ "$status_code" = "200" ] && echo "$response" | grep -q "choices"; then
        increment_test 0
        echo "  📊 Respuesta recibida: $(echo "$response" | jq -r '.choices[0].message.content' 2>/dev/null | cut -c1-50)..."
    else
        increment_test 1
        echo "  📊 Status: $status_code"
    fi
}

# Función para test de STT endpoint
test_stt_endpoint() {
    echo ""
    echo -e "${BLUE}🎤 Test: Speech-to-Text endpoint${NC}"
    
    echo -n "  Testing /v1/audio/transcriptions-public endpoint... "
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8080/v1/audio/transcriptions-public" 2>/dev/null)
    
    if [ "$status_code" = "405" ] || [ "$status_code" = "422" ]; then
        # 405 = Method Not Allowed (esperado para GET en endpoint POST)
        # 422 = Unprocessable Entity (esperado sin archivo)
        increment_test 0
        echo "  📊 Endpoint disponible (Status: $status_code)"
    else
        increment_test 1
        echo "  📊 Status inesperado: $status_code"
    fi
}

# Función para test de ingestor
test_ingestor_endpoints() {
    echo ""
    echo -e "${BLUE}📄 Test: Ingestor endpoints${NC}"
    
    echo -n "  Testing /health endpoint... "
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8081/health" 2>/dev/null)
    
    if [ "$status_code" = "200" ]; then
        increment_test 0
    else
        increment_test 1
    fi
    
    echo -n "  Testing /process endpoint (GET)... "
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8081/process" 2>/dev/null)
    
    if [ "$status_code" = "405" ] || [ "$status_code" = "422" ]; then
        # 405 = Method Not Allowed (esperado para GET en endpoint POST)
        increment_test 0
    else
        increment_test 1
    fi
}

# Función para test de UI accesibilidad
test_ui_accessibility() {
    echo ""
    echo -e "${BLUE}🖥️ Test: UI accesibilidad${NC}"
    
    echo -n "  Testing UI homepage... "
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8082/" 2>/dev/null)
    
    if [ "$status_code" = "200" ]; then
        increment_test 0
        echo "  📊 UI accesible en http://localhost:8082"
    else
        increment_test 1
        echo "  📊 Status: $status_code"
    fi
}

# Función para test de memoria
test_memory_endpoints() {
    echo ""
    echo -e "${BLUE}🧠 Test: Memory endpoints${NC}"
    
    echo -n "  Testing /memory/conversations endpoint... "
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8080/memory/conversations" 2>/dev/null)
    
    if [ "$status_code" = "422" ] || [ "$status_code" = "400" ]; then
        # 422/400 = Bad Request (esperado sin parámetros)
        increment_test 0
    else
        increment_test 1
        echo "  📊 Status: $status_code"
    fi
}

# Función para test de conectividad entre servicios
test_service_connectivity() {
    echo ""
    echo -e "${BLUE}🔗 Test: Conectividad entre servicios${NC}"
    
    echo -n "  Testing Gateway → Ingestor connectivity... "
    
    # Simular una llamada interna del Gateway al Ingestor
    local test_payload='{"test": true}'
    local response=$(curl -s -X POST "http://localhost:8080/files/test-user" \
        -H "Content-Type: application/json" \
        -d "$test_payload" 2>/dev/null)
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8080/files/test-user" \
        -H "Content-Type: application/json" \
        -d "$test_payload" 2>/dev/null)
    
    # Esperamos algún tipo de respuesta (no necesariamente 200)
    if [ "$status_code" != "000" ] && [ "$status_code" != "502" ] && [ "$status_code" != "503" ]; then
        increment_test 0
    else
        increment_test 1
    fi
}

# Función para test de variables de entorno
test_environment_variables() {
    echo ""
    echo -e "${BLUE}⚙️ Test: Variables de entorno${NC}"
    
    echo -n "  Testing environment detection... "
    
    # Verificar que los servicios detectan el entorno local
    local gateway_env=$(curl -s "http://localhost:8080/health" 2>/dev/null | grep -o '"environment":"[^"]*"' 2>/dev/null || echo "")
    
    if echo "$gateway_env" | grep -q "local"; then
        increment_test 0
    else
        increment_test 1
        echo "  📊 Gateway env: $gateway_env"
    fi
}

# Función para mostrar resumen de tests
show_test_summary() {
    echo ""
    echo -e "${BLUE}📊 RESUMEN DE TESTS${NC}"
    echo "=================="
    echo ""
    echo -e "Total de tests: ${BLUE}$TESTS_TOTAL${NC}"
    echo -e "Tests pasados: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests fallidos: ${RED}$TESTS_FAILED${NC}"
    echo ""
    
    local success_rate=$((TESTS_PASSED * 100 / TESTS_TOTAL))
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 ¡Todos los tests pasaron! (100%)${NC}"
        echo -e "${GREEN}✅ El entorno local está funcionando correctamente${NC}"
        return 0
    elif [ $success_rate -ge 80 ]; then
        echo -e "${YELLOW}⚠️ La mayoría de tests pasaron ($success_rate%)${NC}"
        echo -e "${YELLOW}🔧 Revisa los tests fallidos${NC}"
        return 1
    else
        echo -e "${RED}❌ Muchos tests fallaron ($success_rate%)${NC}"
        echo -e "${RED}🚨 El entorno local necesita atención${NC}"
        return 2
    fi
}

# Función para mostrar información de debugging
show_debug_info() {
    if [ $TESTS_FAILED -gt 0 ]; then
        echo ""
        echo -e "${BLUE}🔧 INFORMACIÓN DE DEBUGGING${NC}"
        echo "=========================="
        echo ""
        echo "📋 Comandos útiles para debugging:"
        echo "  Ver logs de servicios:"
        echo "    docker-compose logs -f"
        echo "    docker-compose logs -f corpchat-gateway"
        echo "    docker-compose logs -f corpchat-ingestor"
        echo "    docker-compose logs -f corpchat-ui"
        echo ""
        echo "  Ver estado de contenedores:"
        echo "    docker-compose ps"
        echo "    docker ps"
        echo ""
        echo "  Verificar conectividad:"
        echo "    curl http://localhost:8080/health"
        echo "    curl http://localhost:8081/health"
        echo "    curl http://localhost:8082/health"
        echo ""
        echo "  Reiniciar servicios:"
        echo "    docker-compose restart"
        echo "    ./scripts/start_local.sh"
        echo ""
    fi
}

# Función principal
main() {
    echo -e "${BLUE}🎯 Ejecutando tests E2E para desarrollo local...${NC}"
    echo ""
    
    # Cambiar al directorio del proyecto
    cd "$PROJECT_ROOT"
    
    # Verificar que los servicios estén corriendo
    if ! check_services_running; then
        echo -e "${RED}❌ Los servicios no están corriendo${NC}"
        echo -e "${YELLOW}💡 Ejecuta ./scripts/start_local.sh primero${NC}"
        exit 1
    fi
    
    # Esperar un momento para que los servicios se estabilicen
    echo -e "${BLUE}⏳ Esperando que los servicios se estabilicen...${NC}"
    sleep 5
    
    # Ejecutar tests
    test_basic_connectivity
    test_models_endpoint
    test_chat_completions
    test_stt_endpoint
    test_ingestor_endpoints
    test_ui_accessibility
    test_memory_endpoints
    test_service_connectivity
    test_environment_variables
    
    # Mostrar resumen
    local exit_code
    show_test_summary
    exit_code=$?
    
    # Mostrar información de debugging si es necesario
    show_debug_info
    
    exit $exit_code
}

# Manejar señales de interrupción
trap 'echo ""; echo -e "${YELLOW}🛑 Tests interrumpidos por usuario${NC}"; exit 1' INT

# Ejecutar función principal
main "$@"
