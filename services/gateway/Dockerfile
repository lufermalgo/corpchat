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
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app.py .

# Variables de entorno por defecto
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Exponer puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health')"

# Comando de inicio
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT} --workers 1

