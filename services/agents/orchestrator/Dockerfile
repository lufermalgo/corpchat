# Dockerfile para Orquestador ADK
FROM python:3.13-slim

# Metadata
LABEL maintainer="CorpChat Team"
LABEL service="orchestrator"

# Configurar workdir
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements del workspace agents (context es services)
COPY agents/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar shared utilities
COPY agents/shared /app/shared

# Copiar código del orquestador
COPY agents/orchestrator/agent.py agents/orchestrator/main.py agents/orchestrator/__init__.py /app/

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
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1

