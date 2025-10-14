# CorpChat MVP

**Plataforma Conversacional Corporativa** - Arquitectura Serverless con ADK + Open WebUI en GCP

## 🎯 Objetivo

Chat corporativo con SSO Google (IAP), agentes Gemini vía ADK, adjuntos por chat con procesamiento completo de documentos, y mini-RAG con embeddings en Firestore. Todo con **costo base = 0** (pay-per-use estricto).

## 🏗️ Arquitectura

- **Frontend**: Open WebUI personalizado en Cloud Run + IAP (SSO Google Workspace)
- **Gateway**: API OpenAI-compatible → Vertex AI Gemini con streaming
- **Orquestación**: ADK con agente principal + especialistas (multi-agent)
- **Procesamiento**: Pipeline completo de documentos (PDF, DOCX, XLSX, imágenes) con OCR, detección de tablas, chunking semántico y embeddings
- **Tools**: Docs Tool, Sheets Tool (OpenAPI endpoints)
- **Almacenamiento**: Firestore (metadata, chunks, vectores), GCS (artifacts, adjuntos)
- **FinOps**: Budgets, guardrails, auto-apagado dev/stage, observabilidad de costos

## 📦 Estructura del Proyecto

```
CorpChat/
├── docs/                    # Documentación técnica
├── references/              # Repos de referencia (ADK, Open WebUI)
├── infra/                   # Terraform e IaC
├── services/                # Servicios deployables
│   ├── ui/                  # Open WebUI personalizado
│   ├── gateway/             # Gateway OpenAI → Gemini
│   ├── agents/              # Workspace ADK (orchestrator + specialists)
│   ├── ingestor/            # Pipeline procesamiento docs
│   └── tools/               # Tool Servers
└── tests/                   # Tests E2E y dataset canario
```

## 🚀 Setup Rápido

### Prerrequisitos

- Python 3.13
- Docker
- `gcloud` CLI configurado
- Acceso al proyecto GCP `genai-385616`
- Google Workspace para IAP

### Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/lufermalgo/corpchat.git
   cd corpchat
   ```

2. **Clonar referencias (solo para consulta, no se commitean):**
   ```bash
   mkdir -p references
   cd references
   git clone https://github.com/google/adk-python.git adk-python-ref
   git clone https://github.com/open-webui/open-webui.git open-webui-base
   git clone https://github.com/open-webui/docs.git open-webui-docs
   cd ..
   ```

3. **Configurar GCP:**
   ```bash
   gcloud config set project genai-385616
   gcloud config set run/region us-central1
   ./infra/scripts/setup_gcp.sh
   ```

4. **Crear entornos virtuales por servicio:**
   ```bash
   # Gateway
   cd services/gateway
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   deactivate
   cd ../..

   # Agents (ADK)
   cd services/agents
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install google-genai-adk==1.8.0
   pip install -r requirements.txt
   deactivate
   cd ../..

   # Ingestor
   cd services/ingestor
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   deactivate
   cd ../..

   # Tools
   cd services/tools
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   deactivate
   cd ../..
   ```

5. **Configurar variables de entorno:**
   ```bash
   cp .env.template .env
   # Editar .env con tus valores
   ```

## 📚 Documentación

- [Arquitectura](docs/architecture.md)
- [Integración ADK](docs/adk-integration.md)
- [Deployment](docs/deployment.md)

## 🧪 Testing

### Tests unitarios
```bash
cd services/ingestor
source .venv/bin/activate
pytest tests/
```

### Tests E2E
```bash
cd tests/e2e
source ../../services/gateway/.venv/bin/activate
pytest test_full_flow.py
```

## 🚀 Deployment

Cada servicio tiene su propio `cloudbuild.yaml` para CI/CD:

```bash
# Ejemplo: Deploy gateway
gcloud builds submit services/gateway --config=services/gateway/cloudbuild.yaml
```

## 📊 FinOps y Observabilidad

- **Budgets**: Configurados con thresholds 50/80/100%
- **Guardrails**: Auto-reducción de instancias y bloqueo de rutas costosas
- **Dashboards**: Cloud Monitoring con métricas de costo por chat, tokens, latencia
- **Auto-apagado**: Dev/stage apagan automáticamente noches y fines de semana

## 🔒 Seguridad

- IAP/SSO para autenticación (Google Workspace)
- Secret Manager para credenciales
- IAM con least privilege
- Signed URLs para GCS
- No secrets en código

## 🤝 Contribución

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías de desarrollo.

## 📄 Licencia

[Definir licencia]

## 🙋 Soporte

[Definir canal de soporte]

---

**Proyecto**: CorpChat MVP  
**Stack**: ADK (Google Genai) + Open WebUI + GCP (Cloud Run, Vertex AI, Firestore, GCS)  
**Principio**: Costo base = 0 (100% serverless, pay-per-use)

