#!/bin/bash

# Script para iniciar servicios localmente usando Python directamente
# Alternativa cuando Docker tiene problemas de filesystem

set -e

echo "🚀 Iniciando CorpChat en modo desarrollo local (Python directo)"
echo "================================================================"

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements-local.txt" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio raíz del proyecto"
    exit 1
fi

# Activar entorno virtual
if [ -f "activate_env.sh" ]; then
    echo "📦 Activando entorno virtual..."
    source activate_env.sh
else
    echo "❌ Error: Entorno virtual no encontrado. Ejecuta primero: ./scripts/setup_venv.sh"
    exit 1
fi

# Verificar variables de entorno
if [ ! -f ".env.local" ]; then
    echo "❌ Error: Archivo .env.local no encontrado. Cópialo desde env.local.template"
    exit 1
fi

# Cargar variables de entorno
echo "🔧 Cargando variables de entorno..."
export $(cat .env.local | grep -v '^#' | xargs)

# Verificar credenciales
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "❌ Error: GOOGLE_APPLICATION_CREDENTIALS no está configurado"
    exit 1
fi

if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "❌ Error: Archivo de credenciales no encontrado: $GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi

echo "✅ Credenciales verificadas: $GOOGLE_APPLICATION_CREDENTIALS"

# Función para matar procesos al salir
cleanup() {
    echo "🛑 Deteniendo servicios..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Iniciar Gateway
echo "🌐 Iniciando Gateway en puerto 8000..."
cd services/gateway
export ENVIRONMENT=local
export INGESTOR_SERVICE_URL=http://localhost:8080
export SERVICE_NAME=corpchat-local
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload &
GATEWAY_PID=$!

# Esperar un momento para que el Gateway inicie
sleep 3

# Iniciar Ingestor
echo "📄 Iniciando Ingestor en puerto 8080..."
cd ../ingestor
export ENVIRONMENT=local
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload &
INGESTOR_PID=$!

# Volver al directorio raíz
cd ../..

echo ""
echo "🎉 Servicios iniciados exitosamente!"
echo "=================================="
echo "📊 Gateway:     http://localhost:8000"
echo "📄 Ingestor:    http://localhost:8080"
echo "📚 Documentación: http://localhost:8000/docs"
echo ""
echo "💡 Para probar:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8080/health"
echo ""
echo "🛑 Presiona Ctrl+C para detener todos los servicios"
echo ""

# Esperar a que los procesos terminen
wait $GATEWAY_PID $INGESTOR_PID
