# Variables de Entorno CorpChat

## 🔧 **CONFIGURACIÓN MULTI-CLIENTE**

Este documento define todas las variables de entorno requeridas para el despliegue multi-cliente de CorpChat. **NO HAY VALORES HARDCODED** en el código.

## 📋 **VARIABLES REQUERIDAS**

### **Variables de Infraestructura**

| Variable | Descripción | Ejemplo | Requerida |
|----------|-------------|---------|-----------|
| `GOOGLE_CLOUD_PROJECT` | ID del proyecto GCP | `cliente-abc-123` | ✅ |
| `GOOGLE_CLOUD_LOCATION` | Región de GCP | `us-central1` | ✅ |
| `GCS_BUCKET_ATTACHMENTS` | Bucket para archivos | `cliente-abc-attachments` | ✅ |
| `FIRESTORE_COLLECTION_PREFIX` | Prefijo de colecciones | `cliente_abc` | ✅ |

### **Variables de Servicios**

| Variable | Descripción | Ejemplo | Requerida |
|----------|-------------|---------|-----------|
| `INGESTOR_SERVICE_URL` | URL del servicio Ingestor | `https://cliente-abc-ingestor.run.app` | ✅ |
| `SERVICE_NAME` | Nombre del servicio Gateway | `cliente-abc-gateway` | ✅ |

### **Variables de Modelos**

| Variable | Descripción | Ejemplo | Requerida |
|----------|-------------|---------|-----------|
| `MODEL` | Modelo por defecto | `gemini-2.5-flash-001` | ❌ |
| `VERTEX_LOCATION` | Región de Vertex AI | `us-central1` | ❌ |

## 🚀 **CONFIGURACIÓN POR CLIENTE**

### **Cliente ABC Corp**

```bash
# Infraestructura
export GOOGLE_CLOUD_PROJECT="abc-corp-456"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GCS_BUCKET_ATTACHMENTS="abc-corp-attachments"
export FIRESTORE_COLLECTION_PREFIX="abc_corp"

# Servicios
export INGESTOR_SERVICE_URL="https://abc-corp-ingestor.run.app"
export SERVICE_NAME="abc-corp-gateway"

# Modelos
export MODEL="gemini-2.5-flash-001"
export VERTEX_LOCATION="us-central1"
```

### **Cliente XYZ Inc**

```bash
# Infraestructura
export GOOGLE_CLOUD_PROJECT="xyz-inc-789"
export GOOGLE_CLOUD_LOCATION="europe-west1"
export GCS_BUCKET_ATTACHMENTS="xyz-inc-attachments"
export FIRESTORE_COLLECTION_PREFIX="xyz_inc"

# Servicios
export INGESTOR_SERVICE_URL="https://xyz-inc-ingestor.run.app"
export SERVICE_NAME="xyz-inc-gateway"

# Modelos
export MODEL="gemini-2.5-flash-001"
export VERTEX_LOCATION="europe-west1"
```

## 🔧 **CONFIGURACIÓN EN CLOUD BUILD**

### **Gateway (services/gateway/cloudbuild-simple.yaml)**

```yaml
env:
- name: GOOGLE_CLOUD_PROJECT
  value: $PROJECT_ID
- name: GOOGLE_CLOUD_LOCATION
  value: ${_REGION}
- name: FIRESTORE_COLLECTION_PREFIX
  value: $FIRESTORE_COLLECTION_PREFIX
- name: INGESTOR_SERVICE_URL
  value: $INGESTOR_SERVICE_URL
- name: SERVICE_NAME
  value: $SERVICE_NAME
```

### **Ingestor (services/ingestor/cloudbuild-simple.yaml)**

```yaml
env:
- name: GOOGLE_CLOUD_PROJECT
  value: $PROJECT_ID
- name: GOOGLE_CLOUD_LOCATION
  value: ${_REGION}
- name: GCS_BUCKET_ATTACHMENTS
  value: $GCS_BUCKET_ATTACHMENTS
- name: FIRESTORE_COLLECTION_PREFIX
  value: $FIRESTORE_COLLECTION_PREFIX
```

### **UI (services/ui/cloudbuild-simple.yaml)**

```yaml
env:
- name: OPENAI_API_BASE_URL
  value: $OPENAI_API_BASE_URL  # URL del Gateway
- name: OPENAI_API_KEY
  value: $OPENAI_API_KEY       # Token del Gateway
```

## 📝 **VALIDACIÓN DE VARIABLES**

### **En Gateway (app.py)**

```python
# ✅ VALIDACIÓN CORRECTA
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")

FIRESTORE_COLLECTION_PREFIX = os.getenv("FIRESTORE_COLLECTION_PREFIX")
if not FIRESTORE_COLLECTION_PREFIX:
    raise ValueError("FIRESTORE_COLLECTION_PREFIX environment variable is required")

INGESTOR_SERVICE_URL = os.getenv("INGESTOR_SERVICE_URL")
if not INGESTOR_SERVICE_URL:
    raise ValueError("INGESTOR_SERVICE_URL environment variable is required")
```

### **En Ingestor (main.py)**

```python
# ✅ VALIDACIÓN CORRECTA
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
if not project_id:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")

bucket_name = os.getenv("GCS_BUCKET_ATTACHMENTS")
if not bucket_name:
    raise ValueError("GCS_BUCKET_ATTACHMENTS environment variable is required")
```

## 🚫 **ANTI-PATRONES ELIMINADOS**

### **❌ ANTES (Hardcoded)**

```python
# ❌ MALO - Hardcoded
storage_client = storage.Client(project="genai-385616")
bucket_name = "corpchat-genai-385616-attachments"
vertexai.init(project="genai-385616", location="us-central1")
```

### **✅ AHORA (Dinámico)**

```python
# ✅ BUENO - Variables de entorno
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
if not project_id:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")

bucket_name = os.getenv("GCS_BUCKET_ATTACHMENTS")
if not bucket_name:
    raise ValueError("GCS_BUCKET_ATTACHMENTS environment variable is required")

vertexai.init(project=project_id, location=location)
```

## 🔄 **PROCESO DE REPLICACIÓN**

### **1. Nuevo Cliente**

```bash
# 1. Crear proyecto GCP
gcloud projects create cliente-nuevo-123

# 2. Configurar variables
export GOOGLE_CLOUD_PROJECT="cliente-nuevo-123"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GCS_BUCKET_ATTACHMENTS="cliente-nuevo-attachments"
export FIRESTORE_COLLECTION_PREFIX="cliente_nuevo"

# 3. Desplegar con Terraform
terraform apply -var="project_id=cliente-nuevo-123"

# 4. Desplegar servicios
gcloud builds submit --config services/gateway/cloudbuild-simple.yaml \
  --substitutions=_PROJECT_ID=cliente-nuevo-123
```

### **2. Validación**

```bash
# Verificar que no hay hardcoding
grep -r "genai-385616" services/ || echo "✅ No hardcoding found"
grep -r "corpchat-genai" services/ || echo "✅ No hardcoding found"
grep -r "us-central1" services/ | grep -v "os.getenv" || echo "✅ No hardcoding found"
```

## 📊 **MÉTRICAS DE CALIDAD**

- ✅ **0 valores hardcoded** en código de producción
- ✅ **100% variables de entorno** para configuración
- ✅ **Validación obligatoria** de variables críticas
- ✅ **Documentación completa** de todas las variables
- ✅ **Ejemplos de configuración** por cliente
- ✅ **Proceso de replicación** documentado

## 🎯 **BENEFICIOS**

1. **Multi-cliente**: Un solo código, múltiples deployments
2. **Seguridad**: Sin credenciales en código
3. **Flexibilidad**: Configuración por entorno
4. **Mantenibilidad**: Cambios centralizados
5. **Escalabilidad**: Replicación automática
