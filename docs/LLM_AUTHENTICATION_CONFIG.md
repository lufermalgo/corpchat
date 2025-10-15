# Configuración de LLM y Autenticación - CorpChat

**Última actualización**: 15 Octubre 2025

---

## 🔐 Autenticación: Workload Identity Federation (WIF)

### Service Account Principal
```
Service Account: corpchat-app@genai-385616.iam.gserviceaccount.com
Display Name: CorpChat App Service Account
Unique ID: 101511071625757478113
```

### Roles Asignados
- ✅ `roles/aiplatform.user` - Acceso a Vertex AI (Gemini)
- ✅ `roles/bigquery.dataEditor` - Escribir en BigQuery
- ✅ `roles/bigquery.jobUser` - Ejecutar queries BigQuery
- ✅ `roles/datastore.user` - Acceso a Firestore
- ✅ `roles/secretmanager.secretAccessor` - Leer secrets
- ✅ `roles/storage.objectAdmin` - GCS bucket management

### Configuración WIF
**No se usan API Keys**. Todos los servicios usan **Workload Identity Federation**:

1. **Cloud Run** → Service Account automática
2. **Vertex AI** → Autenticación automática vía WIF
3. **BigQuery** → Sin credenciales explícitas
4. **GCS/Firestore** → WIF transparente

---

## 🤖 Modelos LLM Configurados

### 1. Gateway (OpenAI-compatible API)
```python
# services/gateway/app.py
PROJECT_ID = "genai-385616"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.5-flash-001"

# Inicialización
vertexai.init(project=PROJECT_ID, location=LOCATION)
```

**Modelo**: `gemini-2.5-flash-001`
- ✅ Soporte thinking mode
- ✅ Streaming responses
- ✅ OpenAI-compatible format
- ✅ Costo: ~$0.075/1M input tokens

### 2. Orchestrator (ADK Multi-Agent)
```python
# services/agents/orchestrator/agent.py
PROJECT_ID = "genai-385616"
LOCATION = "us-central1"
MODEL = "gemini-2.0-flash"  # ⚠️ Diferente al Gateway
```

**Modelo**: `gemini-2.0-flash`
- ✅ Thinking mode para delegación
- ✅ Multi-agent orchestration
- ✅ Costo: ~$0.075/1M input tokens

### 3. Especialistas (ADK Agents)
```python
# services/agents/specialists/*/agent.py
MODEL = "gemini-2.5-flash-001"  # ⚠️ Diferente al Orchestrator
```

**Modelo**: `gemini-2.5-flash-001`
- ✅ Specialized tools
- ✅ Knowledge search
- ✅ Document processing

### 4. Embeddings (Vector Search)
```python
# services/ingestor/embeddings.py
# services/agents/shared/tools/knowledge_search_tool.py
model = TextEmbeddingModel.from_pretrained("text-embedding-004")
```

**Modelo**: `text-embedding-004`
- ✅ 768 dimensiones
- ✅ Batch processing (hasta 250 textos)
- ✅ Costo: $0.000025/1K tokens

---

## 🔧 Variables de Entorno por Servicio

### Gateway
```yaml
# cloudbuild.yaml
env:
  - name: VERTEX_PROJECT
    value: genai-385616
  - name: VERTEX_LOCATION  
    value: us-central1
  - name: MODEL
    value: gemini-2.5-flash-001
```

### Orchestrator
```yaml
# cloudbuild.yaml
env:
  - name: GOOGLE_CLOUD_PROJECT
    value: genai-385616
  - name: GOOGLE_CLOUD_LOCATION
    value: us-central1
  - name: GOOGLE_GENAI_USE_VERTEXAI
    value: "True"
  - name: MODEL
    value: gemini-2.0-flash
```

### Ingestor
```yaml
# cloudbuild.yaml
env:
  - name: GOOGLE_CLOUD_PROJECT
    value: genai-385616
  - name: GOOGLE_CLOUD_LOCATION
    value: us-central1
  - name: BIGQUERY_DATASET
    value: corpchat
```

---

## ⚠️ Inconsistencias Detectadas

### 1. Modelos Diferentes
- **Gateway**: `gemini-2.5-flash-001`
- **Orchestrator**: `gemini-2.0-flash`
- **Especialistas**: `gemini-2.5-flash-001`

### 2. Variables de Entorno Inconsistentes
- Gateway usa `VERTEX_PROJECT`
- Orchestrator usa `GOOGLE_CLOUD_PROJECT`
- Ingestor usa `GOOGLE_CLOUD_PROJECT`

---

## 🔧 Recomendaciones de Fix

### 1. Estandarizar Modelos
```python
# Todos los servicios deberían usar:
MODEL = "gemini-2.5-flash-001"  # Único modelo para consistency
```

### 2. Estandarizar Variables
```python
# Todos los servicios deberían usar:
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")  
MODEL = os.getenv("MODEL", "gemini-2.5-flash-001")
```

### 3. Actualizar Cloud Build Configs
```yaml
# cloudbuild.yaml (todos los servicios)
env:
  - name: GOOGLE_CLOUD_PROJECT
    value: genai-385616
  - name: GOOGLE_CLOUD_LOCATION
    value: us-central1
  - name: MODEL
    value: gemini-2.5-flash-001
```

---

## 💰 Costos Estimados

### Por Request Típico
- **Gateway**: ~$0.001 (20 tokens input, 100 output)
- **Orchestrator**: ~$0.0005 (10 tokens thinking + delegation)
- **Especialista**: ~$0.001 (20 tokens + tool calls)
- **Embeddings**: ~$0.00001 (500 tokens → 768 dims)

### Total por Conversación
- **RAG Query**: ~$0.002-0.005
- **Document Upload**: ~$0.001 (embeddings)
- **Chat Simple**: ~$0.001

---

## 🔍 Verificación de Configuración

### 1. Verificar Service Account
```bash
gcloud iam service-accounts describe corpchat-app@genai-385616.iam.gserviceaccount.com --project=genai-385616
```

### 2. Verificar Roles
```bash
gcloud projects get-iam-policy genai-385616 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:corpchat-app@genai-385616.iam.gserviceaccount.com"
```

### 3. Verificar Servicios
```bash
# Gateway
gcloud run services describe corpchat-gateway --region=us-central1 --project=genai-385616 --format="value(spec.template.spec.serviceAccountName)"

# Orchestrator  
gcloud run services describe corpchat-orchestrator --region=us-central1 --project=genai-385616 --format="value(spec.template.spec.serviceAccountName)"
```

### 4. Test de Vertex AI
```bash
# Desde Cloud Shell o local con gcloud auth
python3 -c "
import vertexai
from vertexai.generative_models import GenerativeModel
vertexai.init(project='genai-385616', location='us-central1')
model = GenerativeModel('gemini-2.5-flash-001')
print('✅ Vertex AI conectado correctamente')
"
```

---

## 🚨 Troubleshooting

### Error: "No credentials found"
```bash
# Verificar que Cloud Run tiene service account
gcloud run services describe SERVICE_NAME --region=us-central1 --project=genai-385616

# Verificar que service account tiene roles
gcloud projects get-iam-policy genai-385616 --filter="bindings.members:serviceAccount:corpchat-app@genai-385616.iam.gserviceaccount.com"
```

### Error: "Permission denied"
```bash
# Agregar rol faltante
gcloud projects add-iam-policy-binding genai-385616 \
  --member="serviceAccount:corpchat-app@genai-385616.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Error: "Model not found"
```bash
# Verificar modelo disponible
gcloud ai models list --region=us-central1 --project=genai-385616 --filter="displayName:gemini"
```

---

## 📋 Checklist de Configuración

- ✅ Service Account creada
- ✅ Roles asignados (6 roles)
- ✅ Gateway configurado (gemini-2.5-flash-001)
- ✅ Orchestrator configurado (gemini-2.0-flash)
- ✅ Especialistas configurados (gemini-2.5-flash-001)
- ✅ Embeddings configurados (text-embedding-004)
- ⚠️ Modelos inconsistentes (fix pendiente)
- ⚠️ Variables inconsistentes (fix pendiente)

---

**Estado**: 🟡 **FUNCIONAL CON INCONSISTENCIAS**  
**Prioridad Fix**: Media (no crítico, pero mejora consistency)  
**Tiempo Fix**: ~30 minutos

