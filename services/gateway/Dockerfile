# Dockerfile para Gateway OpenAI-compatible → Vertex AI Gemini
FROM python:3.13-slim

# Metadata
LABEL maintainer="CorpChat Team"
LABEL service="gateway"

# Configurar workdir
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY gateway/app.py .
COPY gateway/model_selector.py .
COPY gateway/stt_service.py .
COPY gateway/memory_service.py .

# Crear directorio para credenciales (se montará como volumen)
RUN mkdir -p /app/credentials

# Variables de entorno por defecto
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Variables de entorno para desarrollo local
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account-local.json
ENV GOOGLE_CLOUD_PROJECT=genai-385616
ENV GOOGLE_CLOUD_LOCATION=us-central1

# Exponer puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando de inicio
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT} --workers 1

