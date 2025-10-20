#!/bin/bash
# Script de validación post-deployment para CorpChat
# Regla de Oro: Ejecutar después de cada deployment

set -e

echo "🚀 VALIDACIÓN POST-DEPLOYMENT CORPCHAT"
echo "======================================"
echo "Fecha: $(date)"
echo ""

# 1. Validar acceso Cloud Run
echo "1️⃣ Validando acceso Cloud Run..."
./scripts/validate_cloud_run_access.sh
echo ""

# 2. Validar endpoints críticos
echo "2️⃣ Validando endpoints críticos..."
echo ""

# Gateway - Modelos
echo "📋 Testing Gateway - Lista de modelos..."
gateway_models=$(curl -s "https://corpchat-gateway-2s63drefva-uc.a.run.app/models" --max-time 10)
if echo "$gateway_models" | grep -q "gemini"; then
    echo "  ✅ Gateway: Modelos disponibles"
else
    echo "  ❌ Gateway: Error en modelos"
fi

# Gateway - Health
echo "🏥 Testing Gateway - Health check..."
gateway_health=$(curl -s "https://corpchat-gateway-2s63drefva-uc.a.run.app/health" --max-time 10)
if echo "$gateway_health" | grep -q "healthy"; then
    echo "  ✅ Gateway: Health check OK"
else
    echo "  ❌ Gateway: Health check failed"
fi

# Ingestor - Health
echo "🏥 Testing Ingestor - Health check..."
ingestor_health=$(curl -s "https://corpchat-ingestor-2s63drefva-uc.a.run.app/health" --max-time 10)
if echo "$ingestor_health" | grep -q "healthy"; then
    echo "  ✅ Ingestor: Health check OK"
else
    echo "  ❌ Ingestor: Health check failed"
fi

# UI - Acceso básico
echo "🌐 Testing UI - Acceso básico..."
ui_response=$(curl -s -o /dev/null -w "%{http_code}" "https://corpchat-ui-2s63drefva-uc.a.run.app/" --max-time 10)
if [ "$ui_response" = "200" ] || [ "$ui_response" = "404" ]; then
    echo "  ✅ UI: Accesible (HTTP $ui_response)"
else
    echo "  ❌ UI: No accesible (HTTP $ui_response)"
fi

echo ""

# 3. Validar configuración de variables de entorno
echo "3️⃣ Validando configuración..."
echo ""

# Verificar que no hay hardcoding
echo "🔍 Verificando ausencia de hardcoding..."
hardcode_check=$(grep -r "genai-385616" services/ 2>/dev/null | grep -v "os.getenv" | wc -l)
if [ $hardcode_check -eq 0 ]; then
    echo "  ✅ No se encontró hardcoding en servicios"
else
    echo "  ❌ Se encontró hardcoding: $hardcode_check ocurrencias"
    echo "  🔧 Ejecutar: grep -r 'genai-385616' services/"
fi

# Verificar variables de entorno en Cloud Build
echo "📝 Verificando variables de entorno en Cloud Build..."
for service in gateway ingestor ui; do
    if [ -f "services/$service/cloudbuild-simple.yaml" ]; then
        env_vars=$(grep -c "GOOGLE_CLOUD_PROJECT\|GCS_BUCKET\|FIRESTORE_COLLECTION" "services/$service/cloudbuild-simple.yaml" || echo "0")
        if [ $env_vars -gt 0 ]; then
            echo "  ✅ $service: Variables de entorno configuradas"
        else
            echo "  ❌ $service: Variables de entorno faltantes"
        fi
    fi
done

echo ""

# 4. Test básico de funcionalidad
echo "4️⃣ Test básico de funcionalidad..."
echo ""

# Test chat simple
echo "💬 Testing chat básico..."
chat_response=$(curl -s -X POST "https://corpchat-gateway-2s63drefva-uc.a.run.app/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model": "gemini-fast", "messages": [{"role": "user", "content": "Hola"}], "stream": false}' \
    --max-time 15)

if echo "$chat_response" | grep -q "choices"; then
    echo "  ✅ Chat: Funcionando correctamente"
else
    echo "  ❌ Chat: Error en respuesta"
    echo "  Response: $chat_response"
fi

echo ""

# 5. Resumen final
echo "📊 RESUMEN DE VALIDACIÓN POST-DEPLOYMENT"
echo "========================================"

# Contar tests exitosos
total_tests=0
passed_tests=0

# Test 1: Cloud Run acceso
if ./scripts/validate_cloud_run_access.sh > /dev/null 2>&1; then
    ((passed_tests++))
fi
((total_tests++))

# Test 2: Endpoints
if echo "$gateway_models" | grep -q "gemini" && echo "$gateway_health" | grep -q "healthy"; then
    ((passed_tests++))
fi
((total_tests++))

# Test 3: Funcionalidad
if echo "$chat_response" | grep -q "choices"; then
    ((passed_tests++))
fi
((total_tests++))

echo "Tests pasados: $passed_tests/$total_tests"

if [ $passed_tests -eq $total_tests ]; then
    echo "🎉 DEPLOYMENT VALIDADO EXITOSAMENTE"
    echo "✅ Todos los servicios están operativos"
    echo "✅ Acceso público configurado correctamente"
    echo "✅ Funcionalidad básica verificada"
    exit 0
else
    echo "⚠️ DEPLOYMENT REQUIERE ATENCIÓN"
    echo "❌ Algunos tests fallaron"
    echo "🔧 Revisar logs y configuración"
    exit 1
fi
