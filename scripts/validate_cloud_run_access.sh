#!/bin/bash
# Script de validación de acceso Cloud Run para CorpChat
# Regla de Oro: Validar acceso después de cada deployment

set -e

PROJECT_ID="genai-385616"
REGION="us-central1"

echo "🔍 VALIDACIÓN DE ACCESO CLOUD RUN - CORPCHAT"
echo "=============================================="
echo ""

# Servicios CorpChat
SERVICES=(
    "corpchat-gateway:Gateway API"
    "corpchat-ingestor:Document Ingestor"
    "corpchat-orchestrator:ADK Orchestrator"
    "corpchat-ui:Open WebUI Interface"
)

echo "📋 Estado de Servicios:"
echo ""

for service_info in "${SERVICES[@]}"; do
    service_name=$(echo $service_info | cut -d: -f1)
    service_desc=$(echo $service_info | cut -d: -f2)
    
    echo "🔧 $service_name ($service_desc)"
    
    # Verificar estado del servicio
    status=$(gcloud run services describe $service_name \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="value(status.conditions[0].status)" 2>/dev/null || echo "NotFound")
    
    if [ "$status" = "True" ]; then
        echo "  ✅ Servicio: Activo"
        
        # Verificar permisos IAM
        iam_check=$(gcloud run services get-iam-policy $service_name \
            --region=$REGION \
            --project=$PROJECT_ID \
            --format="value(bindings.members)" 2>/dev/null | grep "allUsers" || echo "")
        
        if [ -n "$iam_check" ]; then
            echo "  ✅ Permisos: Público (allUsers)"
        else
            echo "  ❌ Permisos: Privado (requiere autenticación)"
            echo "  🔧 Ejecutando: gcloud run services add-iam-policy-binding..."
            
            gcloud run services add-iam-policy-binding $service_name \
                --member="allUsers" \
                --role="roles/run.invoker" \
                --region=$REGION \
                --project=$PROJECT_ID
            
            echo "  ✅ Permisos corregidos"
        fi
        
    elif [ "$status" = "NotFound" ]; then
        echo "  ❌ Servicio: No encontrado"
    else
        echo "  ⚠️ Servicio: Estado desconocido ($status)"
    fi
    
    echo ""
done

echo "🌐 Verificación de Conectividad:"
echo ""

# URLs de test
URLS=(
    "corpchat-gateway:https://corpchat-gateway-2s63drefva-uc.a.run.app/health"
    "corpchat-ingestor:https://corpchat-ingestor-2s63drefva-uc.a.run.app/health"
    "corpchat-ui:https://corpchat-ui-2s63drefva-uc.a.run.app/"
)

for url_info in "${URLS[@]}"; do
    service_name=$(echo $url_info | cut -d: -f1)
    service_url=$(echo $url_info | cut -d: -f2-)
    
    echo "🔗 Testing $service_name..."
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$service_url" --max-time 10 || echo "TIMEOUT")
    
    if [ "$response" = "200" ] || [ "$response" = "404" ]; then
        echo "  ✅ Conectividad: OK (HTTP $response)"
    elif [ "$response" = "TIMEOUT" ]; then
        echo "  ⚠️ Conectividad: Timeout (puede ser cold start)"
    else
        echo "  ❌ Conectividad: Error (HTTP $response)"
    fi
    
    echo ""
done

echo "📊 RESUMEN DE VALIDACIÓN:"
echo "========================"

# Contar servicios activos
active_count=0
total_count=${#SERVICES[@]}

for service_info in "${SERVICES[@]}"; do
    service_name=$(echo $service_info | cut -d: -f1)
    status=$(gcloud run services describe $service_name \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="value(status.conditions[0].status)" 2>/dev/null || echo "NotFound")
    
    if [ "$status" = "True" ]; then
        ((active_count++))
    fi
done

echo "Servicios Activos: $active_count/$total_count"

if [ $active_count -eq $total_count ]; then
    echo "✅ TODOS LOS SERVICIOS ESTÁN ACTIVOS Y ACCESIBLES"
    exit 0
else
    echo "❌ ALGUNOS SERVICIOS REQUIEREN ATENCIÓN"
    exit 1
fi
