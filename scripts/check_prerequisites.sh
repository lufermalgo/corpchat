#!/bin/bash

# Script de verificación de prerequisitos para desarrollo local de CorpChat
# Verifica que la máquina tenga todos los componentes necesarios

echo "🔍 VERIFICACIÓN DE PREREQUISITOS PARA CORPCHAT LOCAL DEVELOPMENT"
echo "=================================================================="
echo ""

# Variables
ERRORS=0
WARNINGS=0

# Función para verificar comandos
check_command() {
    local cmd=$1
    local name=$2
    local min_version=$3
    
    if command -v "$cmd" >/dev/null 2>&1; then
        local version=$(command "$cmd" --version 2>/dev/null | head -n1 || echo "unknown")
        echo "✅ $name: Instalado - $version"
        return 0
    else
        echo "❌ $name: NO INSTALADO"
        ((ERRORS++))
        return 1
    fi
}

# Función para verificar versiones específicas
check_python_version() {
    if command -v python3 >/dev/null 2>&1; then
        local version=$(python3 --version | cut -d' ' -f2)
        local major=$(echo $version | cut -d'.' -f1)
        local minor=$(echo $version | cut -d'.' -f2)
        
        if [ "$major" -ge 3 ] && [ "$minor" -ge 12 ]; then
            echo "✅ Python 3.12+: Instalado - $version"
            return 0
        else
            echo "❌ Python 3.12+: Requerido, pero encontrado $version"
            ((ERRORS++))
            return 1
        fi
    else
        echo "❌ Python 3.12+: NO INSTALADO"
        ((ERRORS++))
        return 1
    fi
}

# Función para verificar Docker
check_docker() {
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            local version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
            echo "✅ Docker: Instalado y funcionando - $version"
            return 0
        else
            echo "⚠️ Docker: Instalado pero no está corriendo"
            ((WARNINGS++))
            return 1
        fi
    else
        echo "❌ Docker: NO INSTALADO"
        ((ERRORS++))
        return 1
    fi
}

# Función para verificar Docker Compose
check_docker_compose() {
    if command -v docker-compose >/dev/null 2>&1; then
        local version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        echo "✅ Docker Compose: Instalado - $version"
        return 0
    elif docker compose version >/dev/null 2>&1; then
        local version=$(docker compose version --short)
        echo "✅ Docker Compose (plugin): Instalado - $version"
        return 0
    else
        echo "❌ Docker Compose: NO INSTALADO"
        ((ERRORS++))
        return 1
    fi
}

# Función para verificar gcloud
check_gcloud() {
    if command -v gcloud >/dev/null 2>&1; then
        local version=$(gcloud --version | head -n1 | cut -d' ' -f4)
        echo "✅ Google Cloud CLI: Instalado - $version"
        
        # Verificar autenticación
        if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
            local account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
            echo "✅ Google Cloud Auth: Autenticado como $account"
        else
            echo "⚠️ Google Cloud Auth: NO AUTENTICADO"
            echo "   Ejecutar: gcloud auth login"
            ((WARNINGS++))
        fi
        
        # Verificar proyecto configurado
        local project=$(gcloud config get-value project 2>/dev/null)
        if [ -n "$project" ]; then
            echo "✅ Google Cloud Project: Configurado - $project"
        else
            echo "⚠️ Google Cloud Project: NO CONFIGURADO"
            echo "   Ejecutar: gcloud config set project YOUR_PROJECT_ID"
            ((WARNINGS++))
        fi
        
        return 0
    else
        echo "❌ Google Cloud CLI: NO INSTALADO"
        ((ERRORS++))
        return 1
    fi
}

# Función para verificar espacio en disco
check_disk_space() {
    local required_gb=10
    local available_gb
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        available_gb=$(df -h . | awk 'NR==2 {print $4}' | sed 's/Gi//' | cut -d'.' -f1)
    else
        # Linux
        available_gb=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//' | cut -d'.' -f1)
    fi
    
    if [ "$available_gb" -ge "$required_gb" ]; then
        echo "✅ Espacio en disco: Suficiente - ${available_gb}GB disponibles"
        return 0
    else
        echo "⚠️ Espacio en disco: Solo ${available_gb}GB disponibles (recomendado: ${required_gb}GB+)"
        ((WARNINGS++))
        return 1
    fi
}

# Función para verificar puertos
check_ports() {
    local ports=(8080 8081 8082)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -i :$port >/dev/null 2>&1 || netstat -an | grep -q ":$port "; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -eq 0 ]; then
        echo "✅ Puertos disponibles: 8080, 8081, 8082 están libres"
        return 0
    else
        echo "⚠️ Puertos ocupados: ${occupied_ports[*]}"
        echo "   Los siguientes servicios pueden estar usando estos puertos:"
        for port in "${occupied_ports[@]}"; do
            echo "   Puerto $port: $(lsof -i :$port 2>/dev/null | awk 'NR==2 {print $1}' || echo 'Proceso desconocido')"
        done
        ((WARNINGS++))
        return 1
    fi
}

# Función para verificar memoria
check_memory() {
    local required_gb=4
    local available_gb
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        available_gb=$(sysctl -n hw.memsize | awk '{print int($0/1024/1024/1024)}')
    else
        # Linux
        available_gb=$(free -g | awk '/^Mem:/ {print $2}')
    fi
    
    if [ "$available_gb" -ge "$required_gb" ]; then
        echo "✅ Memoria RAM: Suficiente - ${available_gb}GB disponibles"
        return 0
    else
        echo "⚠️ Memoria RAM: Solo ${available_gb}GB disponibles (recomendado: ${required_gb}GB+)"
        ((WARNINGS++))
        return 1
    fi
}

# Función para verificar git
check_git() {
    if command -v git >/dev/null 2>&1; then
        local version=$(git --version | cut -d' ' -f3)
        echo "✅ Git: Instalado - $version"
        
        # Verificar configuración básica
        if git config user.name >/dev/null 2>&1 && git config user.email >/dev/null 2>&1; then
            local name=$(git config user.name)
            local email=$(git config user.email)
            echo "✅ Git Config: Configurado - $name <$email>"
        else
            echo "⚠️ Git Config: NO CONFIGURADO"
            echo "   Ejecutar: git config --global user.name 'Tu Nombre'"
            echo "   Ejecutar: git config --global user.email 'tu@email.com'"
            ((WARNINGS++))
        fi
        
        return 0
    else
        echo "❌ Git: NO INSTALADO"
        ((ERRORS++))
        return 1
    fi
}

# Ejecutar verificaciones
echo "📋 VERIFICANDO HERRAMIENTAS BÁSICAS..."
echo "======================================"
check_python_version
check_command "pip3" "Pip3"
check_git

echo ""
echo "🐳 VERIFICANDO DOCKER..."
echo "========================"
check_docker
check_docker_compose

echo ""
echo "☁️ VERIFICANDO GOOGLE CLOUD..."
echo "=============================="
check_gcloud

echo ""
echo "💻 VERIFICANDO RECURSOS DEL SISTEMA..."
echo "====================================="
check_memory
check_disk_space
check_ports

echo ""
echo "📊 RESUMEN DE VERIFICACIÓN"
echo "=========================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "🎉 TODOS LOS PREREQUISITOS CUMPLIDOS"
    echo "✅ Tu máquina está lista para desarrollo local de CorpChat"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️ PREREQUISITOS CUMPLIDOS CON ADVERTENCIAS"
    echo "✅ Puedes proceder con el desarrollo, pero considera resolver las advertencias"
    echo "📝 Advertencias: $WARNINGS"
    exit 0
else
    echo "❌ PREREQUISITOS FALTANTES"
    echo "🚫 No puedes proceder hasta resolver los errores críticos"
    echo "📝 Errores críticos: $ERRORS"
    echo "📝 Advertencias: $WARNINGS"
    echo ""
    echo "🔧 PRÓXIMOS PASOS:"
    echo "1. Instalar las herramientas faltantes"
    echo "2. Ejecutar este script nuevamente"
    echo "3. Seguir la guía de setup en docs/LOCAL_DEVELOPMENT_GUIDE.md"
    exit 1
fi
