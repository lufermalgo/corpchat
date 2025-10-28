# Agent UI - Cognitive Core

Interfaz web simple para interactuar con agentes ADK usando Gradio.

## Características

- ✅ Interfaz de chat web moderna
- ✅ Se conecta a agentes en contenedores separados
- ✅ Historial de conversación
- ✅ Fácil de extender

## Estructura

```
agent-ui/
├── app.py              # Interfaz Gradio
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Acceso

- **UI Web**: http://localhost:7860

## Comandos

### Levantar servicio
```bash
docker-compose up -d --build
```

### Ver logs
```bash
docker logs -f corpchat-agent-ui
```

### Detener servicio
```bash
docker-compose down
```

## Arquitectura

```
┌──────────────────────┐
│   agent-ui :7860     │
│   (Gradio UI)        │
└──────────┬───────────┘
           │ HTTP
           ▼
┌──────────────────────┐
│ base-agent :8080     │
│   (Agent API)        │
└──────────────────────┘
```

## Próximos Pasos

- [ ] Agregar soporte para múltiples agentes
- [ ] Añadir adjuntar archivos
- [ ] Implementar streaming de respuestas
- [ ] Agregar autenticación
