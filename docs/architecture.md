# Arquitectura CorpChat MVP

## Visión General

CorpChat es una plataforma conversacional corporativa serverless construida sobre GCP, utilizando Google Genai ADK para orquestación de agentes y Open WebUI como interfaz de usuario. La arquitectura sigue principios FinOps estrictos con **costo base = 0**.

## Principios de Diseño

### 1. Serverless First
- Todos los componentes escalan a 0 sin tráfico
- `min_instances=0` en todos los servicios Cloud Run
- Pay-per-use estricto sin costos en reposo

### 2. Multi-Agent con ADK
- Orquestador principal que coordina especialistas
- Cada especialista es un agente ADK independiente
- Comunicación via HTTP/Pub/Sub

### 3. Seguridad por Defecto
- IAP + SSO Google Workspace para autenticación
- Service Accounts con least privilege
- Signed URLs para acceso a GCS
- Secret Manager para credenciales

### 4. Observabilidad de Costos
- Labels obligatorios en todos los recursos
- Budgets con guardrails automáticos
- Export de billing a BigQuery
- Dashboards de cost-to-serve

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    Google Workspace SSO                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           Identity-Aware Proxy (IAP)                            │
│           Header: X-Goog-Authenticated-User-Email               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Open WebUI (Cloud Run)                                         │
│  - Branding corporativo                                         │
│  - Trusted header auth                                          │
│  - Min instances: 0                                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Gateway OpenAI-compatible (Cloud Run)                          │
│  - API: /v1/chat/completions                                    │
│  - Proxy a Vertex AI Gemini                                     │
│  - Streaming support                                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Orquestador ADK (Cloud Run)                                    │
│  - Gemini 2.5 Flash + Thinking Mode                             │
│  - Routing a especialistas                                      │
│  - Gestión de sesiones                                          │
└────────┬──────────────────┬──────────────────┬──────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Especialista │  │ Especialista │  │ Especialista │
│ Conocimiento │  │   Estado     │  │  Productos   │
│   Empresa    │  │  Técnico     │  │ & Propuestas │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │     Tool Servers (Cloud Run)   │
         │   - Docs Tool (GCS/GDrive)     │
         │   - Sheets Tool                │
         └───────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  Procesamiento de Adjuntos                       │
│                                                                  │
│  Usuario → GCS (signed URL) → Pub/Sub → Ingestor (Cloud Run)   │
│                                              │                   │
│                                              ▼                   │
│                                    ┌──────────────────┐         │
│                                    │   Extractors     │         │
│                                    │  - PDF           │         │
│                                    │  - XLSX          │         │
│                                    │  - DOCX          │         │
│                                    │  - Images (OCR)  │         │
│                                    └────────┬─────────┘         │
│                                             │                   │
│                                             ▼                   │
│                                    ┌──────────────────┐         │
│                                    │   Chunking +     │         │
│                                    │   Embeddings     │         │
│                                    │ (Vertex AI)      │         │
│                                    └────────┬─────────┘         │
│                                             │                   │
│                                             ▼                   │
│                                    ┌──────────────────┐         │
│                                    │   Firestore      │         │
│                                    │  - Chunks + TTL  │         │
│                                    │  - Vectors       │         │
│                                    └──────────────────┘         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       Almacenamiento                             │
│                                                                  │
│  Firestore              Cloud Storage          BigQuery         │
│  - Metadata            - Adjuntos raw          - Billing export │
│  - Chunks              - Artifacts             - Audit logs     │
│  - Vectores            - Lifecycle:            - Métricas       │
│  - Sesiones (TTL)        * 30d → NEARLINE                       │
│                          * 180d → DELETE                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     FinOps & Observabilidad                      │
│                                                                  │
│  - Budgets: 50/80/100% thresholds                              │
│  - Guardrails: Auto-reducción instancias                        │
│  - Cloud Scheduler: Auto-apagado dev/stage                      │
│  - Cloud Monitoring: Dashboards cost-to-serve                   │
│  - Alertas: Spend rate, latencia, errores                       │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes Clave

### Frontend: Open WebUI

**Tecnología**: Imagen Docker derivada de `ghcr.io/open-webui/open-webui:v0.6.32`

**Personalización**:
- Branding corporativo (CSS, favicon, título)
- Autenticación via trusted header (IAP)
- Configuración de provider externo (gateway)

**Despliegue**:
```yaml
Platform: Cloud Run
Min instances: 0
Max instances: 5 (dev), 10 (prod)
Auth: IAP required
Labels: team=corpchat, env=dev, service=ui
```

### Gateway OpenAI-Compatible

**Propósito**: Adaptar API de Vertex AI Gemini a formato OpenAI para compatibilidad con Open WebUI.

**Endpoints**:
- `POST /v1/chat/completions` (streaming support)
- `GET /v1/models`

**Características**:
- Streaming de respuestas
- Propagación de identidad del usuario
- Logging estructurado con labels
- Rate limiting por usuario

**Modelo**: `gemini-2.5-flash-001` (soporta thinking mode)

### Orquestador ADK

**Agente Principal**: Gemini 2.5 Flash con thinking mode habilitado

**Responsabilidades**:
- Análisis de intención del usuario
- Routing a especialistas apropiados
- Gestión de estado de conversación
- Agregación de respuestas

**Comunicación con especialistas**:
- Invocación HTTP directa para baja latencia
- Fallback a Pub/Sub para operaciones asíncronas

**Configuración**:
```yaml
model: gemini-2.5-flash-001
thinking_config:
  enabled: true
  budget_tokens: 1000
sub_agents:
  - conocimiento_empresa
  - estado_tecnico
  - productos_propuestas
tools:
  - docs_tool
  - sheets_tool
```

### Especialistas ADK

#### 1. Conocimiento Empresa
- **Propósito**: RAG sobre base de conocimiento corporativa
- **Fuentes**: Chats promovidos, documentos validados
- **Vector search**: Firestore (MVP), Vertex AI Vector Search (escala)

#### 2. Estado Técnico
- **Propósito**: Consultas sobre estado de sistemas
- **Integración**: APIs de monitoreo (Splunk, Cloud Monitoring)
- **Políticas**: Quotas de costo estrictas

#### 3. Productos & Propuestas
- **Propósito**: Generación de cotizaciones y consultas de catálogo
- **Fuentes**: Google Sheets, Drive
- **Features**: Plantillas de documentos

### Pipeline de Procesamiento de Documentos

**Trigger**: Upload a GCS → evento `finalize` → Pub/Sub

**Flujo**:
1. **Router**: Detecta MIME type, valida tamaño, dispatch a extractor
2. **Extractors especializados**:
   - PDF: pdfminer.six + pdfplumber + Camelot (tablas)
   - XLSX: openpyxl + pandas (merged cells resolution)
   - DOCX: python-docx (estructura jerárquica)
   - Images: Tesseract OCR + Vision API
3. **Chunking semántico**: 512-1024 tokens, overlap 20-30%
4. **Embeddings**: Vertex AI `text-embedding-004`
5. **Storage**: Firestore con TTL

**Quality metrics**:
- Extraction success rate ≥ 90% (PDF/DOCX)
- Table parse accuracy ≥ 80%
- OCR confidence tracking

### Tool Servers

**Arquitectura**: Microservicios independientes con API OpenAPI

#### Docs Tool
- **Endpoints**: `/read`, `/search`
- **Fuentes**: GCS, Google Drive (con autorización)
- **Seguridad**: Signed URLs, validación de permisos por usuario

#### Sheets Tool
- **Endpoints**: `/read_range`, `/search`
- **Cache**: Firestore (TTL corto)
- **Rate limiting**: Por usuario y por sheet

## Almacenamiento

### Firestore

**Colecciones**:
```
users/{userId}
  - email, displayName, roles

chats/{chatId}
  - owner, members[], visibility, lastUpdated

attachments/{attachmentId}
  - userId, chatId, gcsPath, status, uploadedAt

chats/{chatId}/chunks/{chunkId}
  - text, vector, page, coords, method, confidence
  - TTL: 7 días (dev), 30 días (prod)
```

**Índices**:
- `chatId` + `timestamp`
- `userId` + `lastUpdated`
- Vector similarity (embedding)

### Cloud Storage

**Buckets**:
```
gs://corpchat-genai-385616-attachments/
  users/{userId}/
    chats/{chatId}/
      raw/{uploadId}_{filename}        # Archivos originales
      artifacts/{artifactId}.{ext}     # Procesados
      tables/{tableId}.csv             # Tablas extraídas
```

**Lifecycle**:
- 30 días → NEARLINE
- 180 días → DELETE

**Access control**: Uniform bucket-level, signed URLs

### BigQuery

**Datasets**:
- `billing_export`: Export automático de facturación
- `audit_logs`: Logs de auditoría
- `metrics`: Métricas de uso agregadas

## FinOps

### Budgets

```yaml
Dev:
  monthly_amount: $50
  thresholds: [0.5, 0.8, 1.0]
  actions:
    - 50%: Email alert
    - 80%: Reducir max_instances a 1
    - 100%: Scale to zero, bloquear rutas

Stage:
  monthly_amount: $100
  thresholds: [0.5, 0.8, 1.0]

Prod:
  monthly_amount: $500
  thresholds: [0.5, 0.8, 1.0]
  actions_per_user: true
```

### Auto-apagado

**Cloud Scheduler jobs**:
- `dev-shutdown`: Lun-Vie 19:00 → scale to 0
- `dev-wakeup`: Lun-Vie 08:00 → restore
- `stage-shutdown`: Fines de semana

### Observabilidad

**Dashboards**:
- Costo por chat
- Tokens por request (p50, p95, p99)
- Latencia por servicio
- Extraction success rate
- MAU/DAU

**Alertas**:
- Spend rate > 110% proyección mensual
- p95 latencia > 5s
- Error rate > 5%
- Extraction failure rate > 10%

## Seguridad

### Autenticación y Autorización

```
Usuario → Google Workspace SSO
       → IAP verifica identidad
       → Header X-Goog-Authenticated-User-Email
       → Open WebUI mapea a usuario interno
       → Permisos en Firestore
```

### Service Accounts

```
corpchat-app@genai-385616.iam.gserviceaccount.com
  Roles:
    - roles/datastore.user
    - roles/storage.objectAdmin
    - roles/secretmanager.secretAccessor
    - roles/aiplatform.user
```

### Secrets Management

- API Keys → Secret Manager
- Configuración sensible → Secret Manager
- Rotación automática (cuando aplique)
- Acceso via Workload Identity

## Escalamiento

### MVP (0-100 usuarios)
- Firestore para vectores
- Cloud Run con max_instances conservadores
- Procesamiento síncrono de documentos

### v0.2 (100-500 usuarios)
- Migrar a Vertex AI Vector Search
- Aumentar max_instances según SLOs
- Procesamiento paralelo con Cloud Run jobs

### v1.0 (500+ usuarios)
- Sharding por cliente/dominio
- CDN para assets estáticos
- Cache distribuido (Memorystore)
- Multi-region deployment

## Referencias

- [Guía de Integración ADK](adk-integration.md)
- [Guía de Deployment](deployment.md)
- [Documento Maestro](../plataforma_conversacional_fin_ops_serverless_adk_open_web_ui.md)

