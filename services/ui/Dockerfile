# Dockerfile para Open WebUI con branding corporativo CorpChat
FROM ghcr.io/open-webui/open-webui:v0.6.32

# Metadata
LABEL maintainer="CorpChat Team"
LABEL service="ui"

# Copiar archivos de branding
COPY branding/ /opt/branding/

# Copiar script de entrypoint personalizado
COPY scripts/entrypoint-branding.sh /entrypoint-branding.sh
RUN chmod +x /entrypoint-branding.sh

# Variables de entorno
ENV APP_TITLE="CorpChat"
ENV WEBUI_AUTH_PROVIDER="trusted_header"

# Usar nuestro entrypoint personalizado
ENTRYPOINT ["/entrypoint-branding.sh"]

