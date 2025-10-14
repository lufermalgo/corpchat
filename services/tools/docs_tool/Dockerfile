# Dockerfile para Docs Tool
FROM python:3.13-slim

LABEL maintainer="CorpChat Team"
LABEL service="docs-tool"

WORKDIR /app

# Copiar requirements del workspace tools
COPY ../requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app.py ./

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health')"

CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT} --workers 1

