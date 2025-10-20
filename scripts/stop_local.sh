#!/bin/bash

# Script para detener desarrollo local de CorpChat
# Detiene todos los servicios Docker Compose

echo "🛑 DETENIENDO DESARROLLO LOCAL DE CORPCHAT"
echo "=========================================="
echo ""

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Función para verificar si Docker Compose está corriendo
check_services_running() {
    echo "🔍 Verificando servicios en ejecución..."
    
    cd "$PROJECT_ROOT"
    
    if docker-compose ps --services --filter "status=running" | grep -q .; then
        echo "✅ Servicios encontrados en ejecución"
        return 0
    else
        echo "ℹ️ No hay servicios en ejecución"
        return 1
    fi
}

# Función para mostrar servicios activos
show_running_services() {
    echo ""
    echo "📊 SERVICIOS ACTIVOS:"
    echo "===================="
    
    cd "$PROJECT_ROOT"
    docker-compose ps
    
    echo ""
}

# Función para detener servicios
stop_services() {
    echo "🛑 Deteniendo servicios..."
    
    cd "$PROJECT_ROOT"
    
    if docker-compose down; then
        echo "✅ Servicios detenidos exitosamente"
        return 0
    else
        echo "❌ Error deteniendo servicios"
        return 1
    fi
}

# Función para limpiar volúmenes (opcional)
cleanup_volumes() {
    echo ""
    read -p "¿Deseas eliminar volúmenes de datos? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🧹 Eliminando volúmenes..."
        
        cd "$PROJECT_ROOT"
        
        if docker-compose down -v; then
            echo "✅ Volúmenes eliminados"
        else
            echo "❌ Error eliminando volúmenes"
        fi
    fi
}

# Función para limpiar imágenes (opcional)
cleanup_images() {
    echo ""
    read -p "¿Deseas eliminar imágenes Docker construidas? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🧹 Eliminando imágenes Docker..."
        
        # Eliminar imágenes específicas de CorpChat
        local images=("corpchat-gateway" "corpchat-ingestor" "corpchat-ui" "corpchat-orchestrator")
        
        for image in "${images[@]}"; do
            if docker images | grep -q "$image"; then
                echo "🗑️ Eliminando imagen: $image"
                docker rmi "$image" 2>/dev/null || echo "⚠️ No se pudo eliminar $image"
            fi
        done
        
        echo "✅ Imágenes eliminadas"
    fi
}

# Función para limpiar contenedores huérfanos
cleanup_orphans() {
    echo ""
    read -p "¿Deseas limpiar contenedores huérfanos? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🧹 Limpiando contenedores huérfanos..."
        
        cd "$PROJECT_ROOT"
        
        if docker-compose down --remove-orphans; then
            echo "✅ Contenedores huérfanos eliminados"
        else
            echo "❌ Error limpiando contenedores huérfanos"
        fi
    fi
}

# Función para mostrar resumen
show_summary() {
    echo ""
    echo "📋 RESUMEN DE LIMPIEZA"
    echo "======================"
    echo ""
    echo "✅ Servicios detenidos"
    echo "✅ Contenedores eliminados"
    echo ""
    echo "💡 COMANDOS ÚTILES:"
    echo "  Ver contenedores: docker ps -a"
    echo "  Ver imágenes: docker images"
    echo "  Ver volúmenes: docker volume ls"
    echo "  Limpiar todo: docker system prune -a"
    echo ""
    echo "🚀 Para reiniciar desarrollo:"
    echo "  ./scripts/start_local.sh"
    echo ""
    echo "📚 Para más información:"
    echo "  docs/LOCAL_DEVELOPMENT_GUIDE.md"
}

# Función para verificar limpieza
verify_cleanup() {
    echo ""
    echo "🔍 Verificando limpieza..."
    
    cd "$PROJECT_ROOT"
    
    local running_containers=$(docker-compose ps --services --filter "status=running" 2>/dev/null | wc -l)
    
    if [ "$running_containers" -eq 0 ]; then
        echo "✅ Todos los servicios han sido detenidos"
        return 0
    else
        echo "⚠️ Algunos servicios aún están en ejecución"
        docker-compose ps
        return 1
    fi
}

# Función principal
main() {
    echo "🎯 Deteniendo desarrollo local de CorpChat..."
    echo ""
    
    # Cambiar al directorio del proyecto
    cd "$PROJECT_ROOT"
    
    # Verificar si hay servicios corriendo
    if check_services_running; then
        show_running_services
        
        # Detener servicios
        if stop_services; then
            echo ""
            
            # Limpiar volúmenes (opcional)
            cleanup_volumes
            
            # Limpiar imágenes (opcional)
            cleanup_images
            
            # Limpiar contenedores huérfanos (opcional)
            cleanup_orphans
            
            # Verificar limpieza
            verify_cleanup
            
            # Mostrar resumen
            show_summary
        else
            echo "❌ Error deteniendo servicios"
            echo "💡 Intenta manualmente: docker-compose down --remove-orphans"
            exit 1
        fi
    else
        echo "ℹ️ No hay servicios para detener"
        echo ""
        
        # Preguntar si quiere limpiar de todos modos
        read -p "¿Deseas limpiar contenedores e imágenes existentes? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cleanup_volumes
            cleanup_images
            cleanup_orphans
            show_summary
        else
            echo "✅ Nada que hacer"
        fi
    fi
}

# Manejar señales de interrupción
trap 'echo ""; echo "🛑 Interrumpido por usuario"; exit 1' INT

# Ejecutar función principal
main "$@"
