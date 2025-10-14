#!/usr/bin/env bash
set -euo pipefail

# Entrypoint personalizado para Open WebUI con branding CorpChat

APP_TITLE="${APP_TITLE:-CorpChat}"

echo "🎨 Aplicando branding CorpChat..."

# Localiza el index.html compilado y su carpeta de assets
INDEX=$(find /app -name "index.html" -type f 2>/dev/null | head -n 1 || true)

if [ -n "$INDEX" ]; then
    ASSETS_DIR="$(dirname "$INDEX")/assets"
    mkdir -p "$ASSETS_DIR"
    
    echo "  📄 Index encontrado: $INDEX"
    echo "  📁 Assets dir: $ASSETS_DIR"
    
    # Inyecta título
    if grep -q "<title>" "$INDEX"; then
        sed -i "s|<title>.*</title>|<title>${APP_TITLE}</title>|" "$INDEX" || true
        echo "  ✅ Título actualizado: ${APP_TITLE}"
    fi
    
    # Inyecta enlace al CSS custom si no existe
    if ! grep -q "custom.css" "$INDEX"; then
        sed -i 's|</head>|<link rel="stylesheet" href="/assets/custom.css" /></head>|' "$INDEX" || true
        echo "  ✅ Custom CSS inyectado"
    fi
    
    # Copia assets de branding
    if [ -f /opt/branding/custom.css ]; then
        cp -f /opt/branding/custom.css "$ASSETS_DIR/" 2>/dev/null || true
        echo "  ✅ custom.css copiado"
    fi
    
    if [ -f /opt/branding/favicon.ico ]; then
        cp -f /opt/branding/favicon.ico "$(dirname "$INDEX")/favicon.ico" 2>/dev/null || true
        echo "  ✅ favicon.ico copiado"
    fi
    
    echo "✨ Branding aplicado exitosamente"
else
    echo "⚠️  No se encontró index.html, omitiendo branding"
fi

echo ""
echo "🚀 Iniciando Open WebUI..."
echo ""

# Arranque del contenedor original de Open WebUI
exec /usr/local/bin/start.sh

