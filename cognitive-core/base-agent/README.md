# Base Agent - Cognitive Core

Agente base implementado con Google ADK, listo para ejecutar en Docker y desplegar en GCP Cloud Run.

## Estructura

```
base-agent/
├── Dockerfile          # Imagen Docker del agente
├── app.py             # Aplicación principal con ADK
├── requirements.txt   # Dependencias Python
└── README.md         # Este archivo
```

## Ejecutar en Docker

### Build y run local

```bash
# Build la imagen
docker build -t corpchat-base-agent .

# Run el contenedor
docker run -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT=genai-385616 \
  -e GOOGLE_CLOUD_REGION=us-central1 \
  corpchat-base-agent
```

### Usando docker-compose

```bash
docker-compose up
```

## Endpoints

- `POST /chat` - Procesar mensajes del usuario
- `GET /health` - Health check
- `GET /` - Información del agente

## Próximos pasos

- [ ] Integrar modelo Gemini
- [ ] Agregar herramientas (tools)
- [ ] Implementar memoria persistente
- [ ] Desplegar a Cloud Run
