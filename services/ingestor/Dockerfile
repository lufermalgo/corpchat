# Dockerfile para Ingestor - Document Processing Pipeline
FROM python:3.12-slim

# Metadata
LABEL maintainer="CorpChat Team"
LABEL service="ingestor"

# Configurar workdir
WORKDIR /app

# Instalar dependencias del sistema (Tesseract + build tools)
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    libgomp1 \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements del ingestor
COPY services/ingestor/requirements.txt ./requirements.txt

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código compartido (agents/shared)
RUN mkdir -p /app/agents
COPY services/agents/shared /app/agents/shared
RUN touch /app/agents/__init__.py

# Copiar código del ingestor
COPY services/ingestor/extractors /app/extractors
COPY services/ingestor/*.py /app/

# Variables de entorno por defecto
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Exponer puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health')"

# Comando de inicio
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 2

