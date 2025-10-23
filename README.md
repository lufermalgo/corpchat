# CorpChat - Plataforma Conversacional Multi-Cliente

## 🎯 Descripción

CorpChat es una plataforma conversacional empresarial basada en Google's Agent Development Kit (ADK) e integrada con Open WebUI. Diseñada para ser **modular, escalable y replicable** para múltiples clientes.

## ✨ Características Principales

- **🤖 Multi-Agent Architecture**: Basada en Google ADK con protocolo A2A
- **🎨 UI Moderna**: Open WebUI con autenticación Google OIDC
- **⚡ Multi-Model Support**: Gemini Fast, Thinking e Images
- **🔧 Configuración Dinámica**: Sistema YAML para personalización
- **🏢 Multi-Cliente**: Replicable para diferentes organizaciones
- **🔄 A2A HTTP**: Comunicación robusta entre agentes
- **🛡️ Fallback Robusto**: Vertex AI directo cuando ADK falla

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Open WebUI    │───▶│  Nginx Gateway  │───▶│   Orchestrator  │───▶│ Agent-Generalist│
│   (Puerto 3000) │    │  (Puerto 8080)  │    │   (Puerto 8000) │    │  (Puerto 8001)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Inicio Rápido

### Prerequisitos
- Docker Desktop 4.0+
- Docker Compose 2.0+
- Google Cloud Platform (GCP) con proyecto activo
- Service Account con permisos de Vertex AI
- Google OAuth 2.0 Client ID y Secret

### Instalación

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd CorpChat

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 3. Ejecutar servicios
docker-compose up --build -d

# 4. Verificar servicios
docker ps | grep chatcorp
```

### Acceso
- **UI**: http://localhost:3000
- **API**: http://localhost:8080/v1
- **Health Check**: http://localhost:8080/health

## 🔧 Configuración

### Variables de Entorno Principales
```bash
PROJECT_PREFIX=chatcorp          # Identificador único del proyecto
GCP_PROJECT_ID=genai-385616      # Proyecto GCP
GOOGLE_CLIENT_ID=360...          # OAuth Client ID
GOOGLE_CLIENT_SECRET=...         # OAuth Client Secret
SECRET_KEY=...                   # Clave secreta para sesiones
```

### Configuración de Modelos
Editar `services/backend/config/models.yaml`:
```yaml
models:
  gemini-fast:
    display_name: "Gemini-Super-Fast"
    description: "Respuestas ultra rápidas y eficientes"
    llm_model: "gemini-2.5-flash-lite"
```

## 📊 Modelos Disponibles

| Modelo | Descripción | Uso Recomendado |
|--------|-------------|-----------------|
| `gemini-fast` | Respuestas rápidas | Consultas generales, respuestas cortas |
| `gemini-thinking` | Razonamiento complejo | Análisis profundo, resolución de problemas |
| `gemini-images` | Análisis visual | Descripción de imágenes, generación visual |

## 🔄 Flujo de Comunicación

### Flujo Principal (A2A HTTP)
```
Usuario → UI → Gateway → Orchestrator → Agent-Generalist → Vertex AI
```

### Flujo de Fallback
```
Usuario → UI → Gateway → Orchestrator → Vertex AI (Directo)
```

## 📁 Estructura del Proyecto

```
CorpChat/
├── services/
│   ├── ui/                    # Open WebUI
│   ├── gateway/               # Nginx Gateway
│   └── backend/
│       ├── src/
│       │   ├── orchestrator/  # Orchestrator ADK Agent
│       │   ├── generalist/    # Generalist ADK Agent
│       │   └── shared/        # Configuración compartida
│       └── config/            # Configuración YAML
├── docs/                      # Documentación
├── credentials/               # Service Account JSON
├── docker-compose.yml         # Orquestación de servicios
└── .env                       # Variables de entorno
```

## 🏢 Replicación Multi-Cliente

Para replicar la plataforma para un nuevo cliente:

1. **Configurar variables de entorno** con `PROJECT_PREFIX` único
2. **Personalizar configuración YAML** (modelos, prompts, agentes)
3. **Configurar credenciales GCP** específicas del cliente
4. **Desplegar con Docker Compose**

Ver [Guía de Replicación](./docs/GUIA_REPLICACION.md) para detalles completos.

## 📚 Documentación

- [Arquitectura Completa](./docs/ARQUITECTURA_BASE_COMPLETA.md)
- [Guía de Replicación](./docs/GUIA_REPLICACION.md)
- [Configuración Google OIDC](./docs/GOOGLE_OAUTH_SETUP.md)
- [Reglas de Oro](./docs/GOLDEN_RULES_COMPLETE.md)

## 🧪 Testing

### Pruebas de API
```bash
# Probar modelo rápido
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hola"}], "model": "gemini-fast"}'

# Verificar modelos disponibles
curl http://localhost:8080/v1/models
```

### Pruebas de UI
1. Abrir http://localhost:3000
2. Autenticarse con Google
3. Seleccionar modelo del dropdown
4. Iniciar conversación

## 🔍 Monitoreo

### Logs
```bash
# Logs de todos los servicios
docker-compose logs -f

# Logs específicos
docker logs chatcorp-orchestrator --tail 50
docker logs chatcorp-agent-generalist --tail 50
```

### Health Checks
```bash
# Verificar estado de servicios
curl http://localhost:8080/health
curl http://localhost:8000/health  # Orchestrator directo
curl http://localhost:8001/health  # Agent-Generalist directo
```

## 🚨 Troubleshooting

### Problemas Comunes

**Error: "Cannot connect to host"**
- Verificar que todos los servicios estén ejecutándose
- Verificar configuración de red Docker

**Error: "Google OIDC authentication failed"**
- Verificar `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`
- Verificar configuración en Google Cloud Console

**Error: "Vertex AI permission denied"**
- Verificar Service Account JSON
- Verificar permisos en GCP

Ver [Guía de Replicación](./docs/GUIA_REPLICACION.md#troubleshooting) para más detalles.

## 🛣️ Roadmap

### ✅ Completado (Fase 1)
- Base funcional con 4 componentes
- A2A HTTP implementado
- Configuración dinámica YAML
- Multi-model support
- Replicabilidad multi-cliente

### 🔄 Próximo (Fase 2)
- Sistema de gestión de agentes especializados
- Contenedores dedicados para agentes
- Import/export de agentes
- UI para gestión de agentes
- A2A real con ADK completo

## 🤝 Contribución

1. Fork el repositorio
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para detalles.

## 📞 Soporte

- **Documentación**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Email**: support@corpchat.com

---

**Versión**: 1.0  
**Última actualización**: 2025-10-23  
**Estado**: Base funcional completada y validada