#!/bin/bash
# Script para verificar health de todos los servicios CorpChat
# Ejecutar desde el root del proyecto

set -e

PROJECT_ID="genai-385616"
REGION="us-central1"

echo "======================================"
echo "CorpChat - Health Check All Services"
echo "======================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para check health
check_service() {
    local service_name=$1
    local health_endpoint=$2
    
    echo -n "Checking $service_name... "
    
    # Obtener URL del servicio
    SERVICE_URL=$(gcloud run services describe $service_name \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format='value(status.url)' 2>/dev/null)
    
    if [ -z "$SERVICE_URL" ]; then
        echo -e "${RED}FAILED${NC} - Service not found"
        return 1
    fi
    
    # Generar token de autenticación
    TOKEN=$(gcloud auth print-identity-token 2>/dev/null)
    
    # Hacer request al health endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "${SERVICE_URL}${health_endpoint}" \
        --max-time 10)
    
    if [ "$HTTP_CODE" -eq 200 ]; then
        echo -e "${GREEN}OK${NC} (HTTP $HTTP_CODE)"
        echo "  URL: $SERVICE_URL"
        return 0
    else
        echo -e "${RED}FAILED${NC} (HTTP $HTTP_CODE)"
        echo "  URL: $SERVICE_URL"
        return 1
    fi
}

# Verificar servicios
echo "Checking Cloud Run services..."
echo ""

SERVICES=(
    "corpchat-gateway:/health"
    "corpchat-ui:/health"
    "corpchat-orchestrator:/health"
    "corpchat-ingestor:/health"
)

PASSED=0
FAILED=0

for service_info in "${SERVICES[@]}"; do
    IFS=':' read -r service_name health_endpoint <<< "$service_info"
    if check_service "$service_name" "$health_endpoint"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
    echo ""
done

# Resumen
echo "======================================"
echo "Summary:"
echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"
echo "======================================"

if [ $FAILED -gt 0 ]; then
    exit 1
fi

exit 0

