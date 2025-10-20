#!/bin/bash

# Script para iniciar desarrollo local de CorpChat
# Inicia todos los servicios usando Docker Compose

echo "🚀 INICIANDO DESARROLLO LOCAL DE CORPCHAT"
echo "=========================================="
echo ""

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Función para verificar prerequisitos
check_prerequisites() {
    echo "🔍 Verificando prerequisitos..."
    
    if [ ! -f "$PROJECT_ROOT/scripts/check_prerequisites.sh" ]; then
        echo "❌ Script de prerequisitos no encontrado"
        exit 1
    fi
    
    if ! "$PROJECT_ROOT/scripts/check_prerequisites.sh"; then
        echo "❌ Prerequisitos no cumplidos"
        exit 1
    fi
    
    echo "✅ Prerequisitos verificados"
}

# Función para verificar archivos de configuración
check_config_files() {
    echo "📋 Verificando archivos de configuración..."
    
    # Verificar que existe .env.local
    if [ ! -f "$PROJECT_ROOT/.env.local" ]; then
        echo "⚠️ Archivo .env.local no encontrado"
        echo "💡 Creando desde template..."
        
        if [ -f "$PROJECT_ROOT/env.local.template" ]; then
            cp "$PROJECT_ROOT/env.local.template" "$PROJECT_ROOT/.env.local"
            echo "✅ Archivo .env.local creado desde template"
            echo "🔧 IMPORTANTE: Edita .env.local y configura las variables necesarias"
            echo "   Especialmente: GOOGLE_APPLICATION_CREDENTIALS"
        else
            echo "❌ Template env.local.template no encontrado"
            exit 1
        fi
    else
        echo "✅ Archivo .env.local encontrado"
    fi
    
    # Verificar que existe docker-compose.yml
    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        echo "❌ Archivo docker-compose.yml no encontrado"
        exit 1
    else
        echo "✅ Archivo docker-compose.yml encontrado"
    fi
    
    # Verificar credenciales (opcional para desarrollo)
    if [ ! -f "$PROJECT_ROOT/credentials/service-account-local.json" ]; then
        echo "⚠️ Credenciales de Service Account no encontradas"
        echo "💡 Configura las credenciales siguiendo docs/LOCAL_AUTH_SETUP.md"
        echo "   O usa autenticación con gcloud auth application-default login"
    else
        echo "✅ Credenciales de Service Account encontradas"
    fi
}

# Función para verificar puertos
check_ports() {
    echo "🔌 Verificando puertos disponibles..."
    
    local ports=(8080 8081 8082)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -i :$port >/dev/null 2>&1; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        echo "⚠️ Puertos ocupados: ${occupied_ports[*]}"
        echo "💡 Deteniendo servicios Docker existentes..."
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" down
        sleep 2
    else
        echo "✅ Puertos disponibles"
    fi
}

# Función para limpiar contenedores anteriores
cleanup_containers() {
    echo "🧹 Limpiando contenedores anteriores..."
    
    # Detener contenedores existentes
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" down --remove-orphans
    
    # Limpiar imágenes no utilizadas (opcional)
    read -p "¿Deseas limpiar imágenes Docker no utilizadas? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -f
        echo "✅ Imágenes limpiadas"
    fi
}

# Función para construir imágenes
build_images() {
    echo "🔨 Construyendo imágenes Docker..."
    
    cd "$PROJECT_ROOT"
    
    # Construir imágenes con --no-cache para desarrollo
    if docker-compose build --no-cache; then
        echo "✅ Imágenes construidas exitosamente"
    else
        echo "❌ Error construyendo imágenes"
        exit 1
    fi
}

# Función para iniciar servicios
start_services() {
    echo "🚀 Iniciando servicios..."
    
    cd "$PROJECT_ROOT"
    
    # Iniciar servicios en background
    if docker-compose up -d; then
        echo "✅ Servicios iniciados exitosamente"
    else
        echo "❌ Error iniciando servicios"
        exit 1
    fi
}

# Función para verificar salud de servicios
check_services_health() {
    echo "🏥 Verificando salud de servicios..."
    
    local services=("corpchat-gateway:8080" "corpchat-ingestor:8081" "corpchat-ui:8082")
    local max_attempts=30
    local attempt=1
    
    for service_port in "${services[@]}"; do
        local service_name=$(echo $service_port | cut -d':' -f1)
        local port=$(echo $service_port | cut -d':' -f2)
        
        echo "⏳ Esperando $service_name en puerto $port..."
        
        while [ $attempt -le $max_attempts ]; do
            if curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
                echo "✅ $service_name está respondiendo"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                echo "❌ $service_name no responde después de $max_attempts intentos"
                echo "📋 Verificando logs..."
                docker-compose logs --tail=20 "$service_name"
                return 1
            fi
            
            sleep 2
            ((attempt++))
        done
        
        attempt=1
    done
    
    echo "✅ Todos los servicios están funcionando"
    return 0
}

# Función para mostrar información de servicios
show_services_info() {
    echo ""
    echo "🎉 SERVICIOS INICIADOS EXITOSAMENTE"
    echo "=================================="
    echo ""
    echo "📊 INFORMACIÓN DE SERVICIOS:"
    echo "  🚪 Gateway: http://localhost:8080"
    echo "  📄 Ingestor: http://localhost:8081"
    echo "  🖥️ UI (Open WebUI): http://localhost:8082"
    echo ""
    echo "🔗 ENDPOINTS ÚTILES:"
    echo "  🏥 Health Checks:"
    echo "    - Gateway: http://localhost:8080/health"
    echo "    - Ingestor: http://localhost:8081/health"
    echo "    - UI: http://localhost:8082/health"
    echo ""
    echo "  📚 APIs:"
    echo "    - Models: http://localhost:8080/v1/models"
    echo "    - Chat: http://localhost:8080/v1/chat/completions"
    echo "    - STT: http://localhost:8080/v1/audio/transcriptions-public"
    echo ""
    echo "📋 COMANDOS ÚTILES:"
    echo "  Ver logs: docker-compose logs -f"
    echo "  Detener: docker-compose down"
    echo "  Reiniciar: docker-compose restart"
    echo "  Estado: docker-compose ps"
    echo ""
    echo "🔧 DESARROLLO:"
    echo "  Los archivos fuente están montados como volúmenes"
    echo "  Los cambios se reflejan automáticamente (hot reload)"
    echo "  Para ver logs específicos: docker-compose logs -f [servicio]"
    echo ""
    echo "💡 SIGUIENTE PASO:"
    echo "  Abre http://localhost:8082 en tu navegador para acceder a CorpChat"
}

# Función para mostrar logs
show_logs() {
    echo ""
    echo "📋 ¿Deseas ver los logs de los servicios?"
    read -p "Mostrar logs en tiempo real? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📋 Mostrando logs (Ctrl+C para salir)..."
        docker-compose logs -f
    fi
}

# Función principal
main() {
    echo "🎯 Iniciando desarrollo local de CorpChat..."
    echo ""
    
    # Cambiar al directorio del proyecto
    cd "$PROJECT_ROOT"
    
    # Ejecutar verificaciones
    check_prerequisites
    echo ""
    
    check_config_files
    echo ""
    
    check_ports
    echo ""
    
    # Limpiar contenedores anteriores
    cleanup_containers
    echo ""
    
    # Construir imágenes
    build_images
    echo ""
    
    # Iniciar servicios
    start_services
    echo ""
    
    # Verificar salud
    if check_services_health; then
        show_services_info
        show_logs
    else
        echo "❌ Algunos servicios no están funcionando correctamente"
        echo "📋 Verifica los logs con: docker-compose logs"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"
