# Organización del Proyecto CorpChat

**Fecha**: 15 de Octubre, 2025  
**Versión**: 1.0

---

## Estructura de Directorios

```
CorpChat/
├── README.md                              # Descripción principal del proyecto
├── IMPLEMENTATION_STATUS_2025-10-15.md    # Estado actual de implementación
├── plataforma_conversacional_fin_ops_serverless_adk_open_web_ui.md  # Arquitectura y plan
├── env.template                           # Template de variables de entorno
│
├── docs/                                  # Documentación técnica
│   ├── audits/                           # Auditorías de GCP y recursos
│   │   ├── AUDIT_SUMMARY_20251014.md
│   │   └── audit_*.txt                   # Logs de auditorías
│   ├── implementation/                    # Documentos de implementación por fase
│   │   └── FASE1_ADK_CORRECTIONS_COMPLETE.md
│   ├── setup/                            # Guías de configuración
│   │   ├── GCP_SETUP_COMPLETE.md
│   │   └── VECTOR_STORE_SETUP_COMPLETE.md
│   ├── IAP_OAUTH_SETUP_GUIDE.md         # Guía OAuth IAP
│   ├── SHARED_PROJECT_SAFETY.md         # Procedimientos de seguridad
│   ├── adk-integration.md               # Integración ADK
│   ├── architecture.md                   # Arquitectura detallada
│   └── deployment.md                     # Guía de deployment
│
├── infra/                                 # Infraestructura como código
│   ├── modules/                          # Módulos Terraform reutilizables
│   │   ├── budgets_guardrails/
│   │   ├── firestore_ttl/
│   │   ├── gcs_bucket_lifecycle/
│   │   └── run_service/
│   └── scripts/                          # Scripts de setup GCP
│       ├── enable_services.sh
│       ├── audit_gcp.sh
│       ├── audit_bigquery.sh
│       ├── setup_gcp.sh
│       └── setup_bigquery_vector_store.sh
│
├── services/                              # Microservicios
│   ├── agents/                           # ADK Agents
│   │   ├── orchestrator/                 # Orquestador principal
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── main.py
│   │   │   ├── Dockerfile
│   │   │   └── cloudbuild.yaml
│   │   ├── shared/                       # Código compartido entre agentes
│   │   │   ├── __init__.py
│   │   │   ├── firestore_client.py
│   │   │   ├── bigquery_vector_search.py
│   │   │   ├── utils.py
│   │   │   └── tools/                    # ADK Tools (funciones Python)
│   │   │       ├── __init__.py
│   │   │       ├── knowledge_search_tool.py
│   │   │       ├── docs_tool_wrapper.py
│   │   │       └── sheets_tool_wrapper.py
│   │   ├── specialists/                  # Agentes especialistas
│   │   │   ├── conocimiento_empresa/
│   │   │   ├── estado_tecnico/
│   │   │   └── productos_propuestas/
│   │   ├── tests/                        # Tests de agentes
│   │   │   └── test_orchestrator_delegation.py
│   │   └── requirements.txt
│   │
│   ├── gateway/                          # Model Gateway (OpenAI-compatible → Gemini)
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   ├── cloudbuild.yaml
│   │   └── requirements.txt
│   │
│   ├── ingestor/                         # Pipeline de procesamiento de documentos
│   │   ├── extractors/                   # Extractores por tipo de archivo
│   │   │   ├── __init__.py
│   │   │   ├── pdf_extractor.py
│   │   │   ├── docx_extractor.py
│   │   │   ├── xlsx_extractor.py
│   │   │   └── image_extractor.py
│   │   ├── tests/                        # Tests del ingestor
│   │   │   └── canary/                   # Dataset canario para tests
│   │   │       ├── pdfs/
│   │   │       ├── docx/
│   │   │       ├── xlsx/
│   │   │       └── images/
│   │   ├── main.py                       # FastAPI app
│   │   ├── router.py                     # Event routing (Pub/Sub → Extractores)
│   │   ├── chunker.py                    # Chunking semántico
│   │   ├── embeddings.py                 # Servicio de embeddings
│   │   ├── storage_manager.py            # Wrapper BigQuery
│   │   ├── pipeline.py                   # Pipeline completo
│   │   ├── Dockerfile
│   │   ├── cloudbuild.yaml
│   │   └── requirements.txt
│   │
│   ├── tools/                            # Tool Servers (HTTP services)
│   │   ├── docs_tool/                    # Servicio para leer GCS/GDrive
│   │   │   ├── app.py
│   │   │   ├── Dockerfile
│   │   │   └── cloudbuild.yaml
│   │   ├── sheets_tool/                  # Servicio para Google Sheets
│   │   │   ├── app.py
│   │   │   ├── Dockerfile
│   │   │   └── cloudbuild.yaml
│   │   └── requirements.txt
│   │
│   └── ui/                               # Open WebUI con branding
│       ├── branding/                     # Assets corporativos
│       │   ├── custom.css
│       │   └── favicon.ico
│       ├── scripts/
│       │   └── entrypoint-branding.sh
│       ├── Dockerfile
│       └── cloudbuild.yaml
│
└── tests/                                 # Tests de integración E2E
    └── e2e/
        └── test_full_flow.py
```

---

## Principios de Organización

### 1. Separación por Responsabilidad

- **`services/`**: Un directorio por microservicio
- **`infra/`**: Infraestructura separada del código de aplicación
- **`docs/`**: Documentación técnica organizada por categoría
- **`tests/`**: Tests de integración globales (E2E)

### 2. Cohesión de Código

- **Tests unitarios** junto a su servicio: `services/agents/tests/`
- **Tests de integración** junto al componente: `services/ingestor/tests/canary/`
- **Tests E2E globales** en raíz: `tests/e2e/`

### 3. ADK Tools vs Tool Servers

**ADK Tools** (`services/agents/shared/tools/`):
- Funciones Python que los agentes importan directamente
- Ejemplo: `search_knowledge_base()`, `read_corporate_document()`
- Uso: `from shared.tools import search_knowledge_base`

**Tool Servers** (`services/tools/`):
- Servicios HTTP independientes con endpoints OpenAPI
- Ejemplo: `corpchat-docs-tool`, `corpchat-sheets-tool`
- Uso: HTTP calls desde ADK Tools wrappers

### 4. Documentación Versionada

**Raíz del proyecto** (máximo 3-4 archivos):
- `README.md` - Descripción general
- `IMPLEMENTATION_STATUS_YYYY-MM-DD.md` - Estado actual
- `plataforma_conversacional_fin_ops_serverless_adk_open_web_ui.md` - Arquitectura

**`docs/`** (organizado por tipo):
- `audits/` - Auditorías y logs
- `implementation/` - Documentos de fases completadas
- `setup/` - Guías de configuración

---

## Convenciones de Nombres

### Archivos Python
- **Módulos**: `snake_case.py`
- **Clases**: `PascalCase`
- **Funciones**: `snake_case`

### Servicios GCP
- **Prefijo**: `corpchat-`
- **Formato**: `corpchat-{servicio}-{env}`
- **Ejemplo**: `corpchat-orchestrator-dev`

### Firestore Collections
- **Prefijo**: `corpchat_`
- **Formato**: `corpchat_{collection}`
- **Ejemplo**: `corpchat_chats`, `corpchat_embeddings`

### BigQuery
- **Dataset**: `corpchat`
- **Tablas**: `embeddings`, `chat_history`, etc.

---

## Archivos Críticos

### No Commitear
- `client_secret_*.json` (OAuth credentials)
- `.env` (variables de entorno locales)
- `*.pyc`, `__pycache__/`
- `.venv/`, `node_modules/`
- Logs temporales `*.log`

### Mantener Actualizados
- `IMPLEMENTATION_STATUS_*.md` - Actualizar con cada hito
- `requirements.txt` - Sincronizar con dependencias reales
- `cloudbuild.yaml` - Mantener alineado con Dockerfile

---

## Workflow de Desarrollo

1. **Desarrollo Local**:
   ```bash
   source .venv/bin/activate
   cd services/{servicio}
   python main.py
   ```

2. **Tests Unitarios**:
   ```bash
   cd services/{servicio}
   pytest tests/
   ```

3. **Deploy a GCP**:
   ```bash
   cd services/{servicio}
   gcloud builds submit --config cloudbuild.yaml
   ```

4. **Tests E2E**:
   ```bash
   pytest tests/e2e/ -v
   ```

---

## Reglas de Oro

1. **Mantener organizado**: Archivos en su carpeta correcta según responsabilidad
2. **Eliminar obsoletos**: Documentos duplicados o desactualizados se eliminan
3. **Documentar cambios**: Actualizar `IMPLEMENTATION_STATUS` con cada hito
4. **Prefijos consistentes**: `corpchat-` para GCP, `corpchat_` para Firestore
5. **Tests obligatorios**: Cada componente debe tener tests antes de merge

---

**Última actualización**: 15 de Octubre, 2025  
**Mantenedor**: AI Agent + Luis Fernando Maldonado

