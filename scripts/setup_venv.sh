#!/bin/bash

# Script para configurar entorno virtual Python para desarrollo local de CorpChat
# Crea .venv y instala todas las dependencias necesarias

echo "🐍 CONFIGURANDO ENTORNO VIRTUAL PYTHON PARA CORPCHAT"
echo "===================================================="
echo ""

# Variables
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements-local.txt"
PYTHON_CMD="python3"

# Función para verificar Python
check_python() {
    if command -v python3 >/dev/null 2>&1; then
        local version=$(python3 --version | cut -d' ' -f2)
        local major=$(echo $version | cut -d'.' -f1)
        local minor=$(echo $version | cut -d'.' -f2)
        
        if [ "$major" -ge 3 ] && [ "$minor" -ge 12 ]; then
            echo "✅ Python encontrado: $version"
            return 0
        else
            echo "❌ Python 3.12+ requerido, pero encontrado $version"
            return 1
        fi
    else
        echo "❌ Python3 no encontrado"
        return 1
    fi
}

# Función para crear entorno virtual
create_venv() {
    echo "📦 Creando entorno virtual en $VENV_DIR..."
    
    if [ -d "$VENV_DIR" ]; then
        echo "⚠️ El entorno virtual ya existe en $VENV_DIR"
        read -p "¿Deseas recrearlo? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️ Eliminando entorno virtual existente..."
            rm -rf "$VENV_DIR"
        else
            echo "📝 Usando entorno virtual existente"
            return 0
        fi
    fi
    
    # Crear entorno virtual
    if $PYTHON_CMD -m venv "$VENV_DIR"; then
        echo "✅ Entorno virtual creado exitosamente"
        return 0
    else
        echo "❌ Error creando entorno virtual"
        return 1
    fi
}

# Función para activar entorno virtual
activate_venv() {
    echo "🔄 Activando entorno virtual..."
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source "$VENV_DIR/Scripts/activate"
    else
        # Unix/Linux/macOS
        source "$VENV_DIR/bin/activate"
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ Entorno virtual activado"
        return 0
    else
        echo "❌ Error activando entorno virtual"
        return 1
    fi
}

# Función para actualizar pip
upgrade_pip() {
    echo "⬆️ Actualizando pip..."
    
    if pip install --upgrade pip; then
        echo "✅ pip actualizado"
        return 0
    else
        echo "❌ Error actualizando pip"
        return 1
    fi
}

# Función para instalar dependencias
install_dependencies() {
    echo "📚 Instalando dependencias desde $REQUIREMENTS_FILE..."
    
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        echo "❌ Archivo $REQUIREMENTS_FILE no encontrado"
        return 1
    fi
    
    # Instalar dependencias
    if pip install -r "$REQUIREMENTS_FILE"; then
        echo "✅ Dependencias instaladas exitosamente"
        return 0
    else
        echo "❌ Error instalando dependencias"
        return 1
    fi
}

# Función para verificar instalación
verify_installation() {
    echo "🔍 Verificando instalación..."
    
    # Verificar que pip funciona
    if pip --version >/dev/null 2>&1; then
        echo "✅ pip funcionando correctamente"
    else
        echo "❌ pip no funciona"
        return 1
    fi
    
    # Verificar algunas dependencias clave
    local key_packages=("fastapi" "uvicorn" "google-cloud-aiplatform" "pydantic")
    
    for package in "${key_packages[@]}"; do
        if pip show "$package" >/dev/null 2>&1; then
            local version=$(pip show "$package" | grep Version | cut -d' ' -f2)
            echo "✅ $package: $version"
        else
            echo "❌ $package: NO INSTALADO"
            return 1
        fi
    done
    
    return 0
}

# Función para mostrar información del entorno
show_environment_info() {
    echo ""
    echo "📊 INFORMACIÓN DEL ENTORNO"
    echo "=========================="
    echo "🐍 Python: $(python --version)"
    echo "📦 pip: $(pip --version)"
    echo "📁 Entorno virtual: $(pwd)/$VENV_DIR"
    echo ""
    echo "🔧 COMANDOS ÚTILES:"
    echo "  Activar entorno: source $VENV_DIR/bin/activate"
    echo "  Desactivar entorno: deactivate"
    echo "  Instalar paquete: pip install <paquete>"
    echo "  Listar paquetes: pip list"
    echo "  Exportar dependencias: pip freeze > requirements.txt"
}

# Función para crear script de activación
create_activation_script() {
    echo "📝 Creando script de activación..."
    
    cat > activate_env.sh << 'EOF'
#!/bin/bash
# Script para activar el entorno virtual de CorpChat

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Entorno virtual CorpChat activado"
    echo "🐍 Python: $(python --version)"
    echo "📦 pip: $(pip --version)"
else
    echo "❌ Entorno virtual no encontrado en .venv/"
    echo "💡 Ejecuta ./scripts/setup_venv.sh primero"
fi
EOF
    
    chmod +x activate_env.sh
    echo "✅ Script de activación creado: ./activate_env.sh"
}

# Ejecutar configuración
main() {
    echo "🚀 Iniciando configuración del entorno virtual..."
    echo ""
    
    # Verificar Python
    if ! check_python; then
        echo "❌ Python 3.12+ es requerido"
        exit 1
    fi
    
    # Crear entorno virtual
    if ! create_venv; then
        echo "❌ Error creando entorno virtual"
        exit 1
    fi
    
    # Activar entorno virtual
    if ! activate_venv; then
        echo "❌ Error activando entorno virtual"
        exit 1
    fi
    
    # Actualizar pip
    if ! upgrade_pip; then
        echo "⚠️ Advertencia: No se pudo actualizar pip"
    fi
    
    # Instalar dependencias
    if ! install_dependencies; then
        echo "❌ Error instalando dependencias"
        exit 1
    fi
    
    # Verificar instalación
    if ! verify_installation; then
        echo "❌ Error en la verificación de instalación"
        exit 1
    fi
    
    # Crear script de activación
    create_activation_script
    
    # Mostrar información
    show_environment_info
    
    echo ""
    echo "🎉 ENTORNO VIRTUAL CONFIGURADO EXITOSAMENTE"
    echo "==========================================="
    echo ""
    echo "📋 PRÓXIMOS PASOS:"
    echo "1. Activar el entorno: source .venv/bin/activate"
    echo "2. Configurar Service Account: docs/LOCAL_AUTH_SETUP.md"
    echo "3. Crear .env.local desde .env.local.template"
    echo "4. Iniciar servicios locales: ./scripts/start_local.sh"
    echo ""
    echo "💡 TIP: Usa './activate_env.sh' para activar rápidamente el entorno"
}

# Ejecutar función principal
main "$@"
