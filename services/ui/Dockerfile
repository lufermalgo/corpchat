# Dockerfile para Open WebUI - Desarrollo Local
FROM ghcr.io/open-webui/open-webui:v0.6.34

# Metadata
LABEL maintainer="CorpChat Team"
LABEL service="ui"

# Variables de entorno básicas
ENV APP_TITLE="CorpChat"
ENV WEBUI_NAME="CorpChat"

# Configuración de branding corporativo
ENV WEBUI_FAVICON_URL="https://openwebui.com/favicon.png"
ENV WEBUI_BANNERS="[]"

# Copiar favicon personalizado (si existe)
COPY ui/static/ /app/static/

# Configurar favicon personalizado
RUN if [ -f /app/static/favicon.png ]; then \
        mkdir -p /app/backend/static && \
        cp /app/static/favicon.png /app/backend/static/favicon.png; \
    fi

ENV ENVIRONMENT=local

# Configuración OAuth Google
ENV ENABLE_OAUTH_SIGNUP=true
ENV GOOGLE_CLIENT_ID="36072227238-u72uom2ciaktets6q1rldcc2msv4m7io.apps.googleusercontent.com"
ENV GOOGLE_CLIENT_SECRET="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"
ENV OAUTH_MERGE_ACCOUNTS_BY_EMAIL=true

# Configuración para desarrollo local
ENV OPENAI_API_BASE_URL=http://corpchat-gateway:8080/v1
ENV OPENAI_API_KEY=corpchat-gateway
ENV OPENAI_API_MODELS=gpt-4o-mini,gpt-4o,gemini-2.5-flash-001,gemini-1.5-flash-001
ENV OPENAI_API_EMBEDDING_MODELS=text-embedding-004

# Configuración STT para desarrollo local
ENV AUDIO_STT_ENGINE=openai
ENV AUDIO_STT_MODEL=whisper-1
ENV AUDIO_STT_OPENAI_API_BASE_URL=http://corpchat-gateway:8080/v1/audio
ENV AUDIO_STT_OPENAI_API_KEY=corpchat-gateway
ENV AUDIO_STT_APPEND_MODE=true
ENV AUDIO_STT_CONTINUOUS_MODE=true

# Configuración de roles y permisos
ENV DEFAULT_USER_ROLE=user
ENV ENABLE_SIGNUP=false
ENV ENABLE_LOGIN_FORM=false
ENV USER_PERMISSIONS_CHAT_MULTIPLE_MODELS=true
ENV USER_PERMISSIONS_WORKSPACE_MODELS_ACCESS=true
ENV BYPASS_MODEL_ACCESS_CONTROL=true

# Configuración de documentos
ENV EXTERNAL_DOCUMENT_LOADER_URL=http://corpchat-ingestor:8080/extract
ENV EXTERNAL_DOCUMENT_LOADER_API_KEY=corpchat-local
ENV CONTENT_EXTRACTION_ENGINE=external
ENV BYPASS_EMBEDDING_AND_RETRIEVAL=true
ENV RAG_ALLOWED_FILE_EXTENSIONS=pdf,docx,doc,xlsx,xls

# Configuración de permisos adicionales
ENV USER_PERMISSIONS_CHAT_MULTIPLE_MODELS=true
ENV ENABLE_USER_ID_HEADER=true
ENV USER_ID_HEADER_NAME=X-User-ID

# Configuración de permisos de características (verificadas con documentación Open WebUI)
ENV USER_PERMISSIONS_FEATURES_NOTES=false
ENV ENABLE_EVALUATION_ARENA_MODELS=false
ENV DEFAULT_PROMPT_SUGGESTIONS="[]"
ENV USER_PERMISSIONS_CHAT_CONTROLS=false
ENV USER_PERMISSIONS_CHAT_TEMPORARY=false
ENV USER_PERMISSIONS_CHAT_TEMPORARY_ENFORCED=false
ENV BYPASS_MODEL_ACCESS_CONTROL=true
ENV USER_PERMISSIONS_CHAT_CALL=false

# Configuración de Text-to-Speech (TTS)
ENV AUDIO_TTS_ENGINE=""

# Configuración de timeouts
ENV AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST=30
ENV AIOHTTP_CLIENT_TIMEOUT_OPENAI_MODEL_LIST=30

# Configuración de Ollama (deshabilitado)
ENV ENABLE_OLLAMA_API=false
ENV OLLAMA_BASE_URL=""

# Configuración de documentos
ENV BYPASS_EMBEDDING_AND_RETRIEVAL=true
ENV RAG_ALLOWED_FILE_EXTENSIONS=pdf,docx,doc,xlsx,xls,jpg,jpeg,png,gif,bmp,tiff
ENV RAG_OPENAI_API_BASE_URL=http://corpchat-gateway:8080
ENV RAG_OPENAI_API_KEY=corpchat-gateway

# Configuración de interfaz
ENV ENABLE_FOLLOW_UP_GENERATION=false
ENV DEFAULT_MODELS=gemini-2.5-flash-001
ENV ENABLE_MESSAGE_RATING=false

# Configuración de streaming
ENV ENABLE_STREAMING=true
ENV CHAT_RESPONSE_STREAM_DELTA_CHUNK_SIZE=16

# Configuración de desarrollo
ENV DEBUG=true
ENV LOG_LEVEL=DEBUG


# Deshabilitar configuración persistente para que las variables de entorno se apliquen
ENV ENABLE_PERSISTENT_CONFIG=false