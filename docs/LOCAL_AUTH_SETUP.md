# 🔐 Configuración de Autenticación Google para Desarrollo Local

Esta guía explica cómo configurar la autenticación de Google Cloud para desarrollo local de CorpChat usando Service Account.

## 📋 Prerequisitos

- Cuenta de Google Cloud Platform con proyecto activo
- Permisos de administrador o editor en el proyecto
- gcloud CLI instalado y configurado
- Proyecto CorpChat configurado en GCP

## 🔧 Paso 1: Crear Service Account

### 1.1 Acceder a Google Cloud Console

```bash
# Abrir Google Cloud Console
gcloud auth login
gcloud config set project genai-385616
```

### 1.2 Crear Service Account

```bash
# Crear Service Account para desarrollo local
gcloud iam service-accounts create corpchat-local-dev \
    --display-name="CorpChat Local Development" \
    --description="Service Account para desarrollo local de CorpChat"
```

### 1.3 Asignar Roles Necesarios

El Service Account necesita los siguientes roles:

```bash
# Vertex AI
gcloud projects add-iam-policy-binding genai-385616 \
    --member="serviceAccount:corpchat-local-dev@genai-385616.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Firestore
gcloud projects add-iam-policy-binding genai-385616 \
    --member="serviceAccount:corpchat-local-dev@genai-385616.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

# BigQuery
gcloud projects add-iam-policy-binding genai-385616 \
    --member="serviceAccount:corpchat-local-dev@genai-385616.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding genai-385616 \
    --member="serviceAccount:corpchat-local-dev@genai-385616.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# Cloud Storage
gcloud projects add-iam-policy-binding genai-385616 \
    --member="serviceAccount:corpchat-local-dev@genai-385616.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Speech-to-Text
gcloud projects add-iam-policy-binding genai-385616 \
    --member="serviceAccount:corpchat-local-dev@genai-385616.iam.gserviceaccount.com" \
    --role="roles/speech.client"

# Cloud Logging
gcloud projects add-iam-policy-binding genai-385616 \
    --member="serviceAccount:corpchat-local-dev@genai-385616.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

# Cloud Monitoring
gcloud projects add-iam-policy-binding genai-385616 \
    --member="serviceAccount:corpchat-local-dev@genai-385616.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter"
```

### 1.4 Descargar Key JSON

```bash
# Crear directorio para credenciales
mkdir -p credentials

# Descargar key JSON
gcloud iam service-accounts keys create credentials/service-account-local.json \
    --iam-account=corpchat-local-dev@genai-385616.iam.gserviceaccount.com
```

## 🔒 Paso 2: Configurar Variables de Entorno

### 2.1 Crear archivo .env.local

```bash
# Copiar template
cp .env.local.template .env.local
```

### 2.2 Configurar variables en .env.local

```bash
# Autenticación Google
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account-local.json
GOOGLE_CLOUD_PROJECT=genai-385616
GOOGLE_CLOUD_LOCATION=us-central1

# Entorno
ENVIRONMENT=local

# Servicios locales
GATEWAY_URL=http://localhost:8080
INGESTOR_URL=http://localhost:8081
UI_URL=http://localhost:8082

# Firestore
FIRESTORE_COLLECTION_PREFIX=corpchat_local

# BigQuery
BIGQUERY_DATASET=corpchat_local
BIGQUERY_TABLE_EMBEDDINGS=embeddings_local

# Cloud Storage
GCS_BUCKET_ATTACHMENTS=corpchat-genai-385616-attachments

# Servicio
SERVICE_NAME=corpchat-local
```

## 🐳 Paso 3: Configurar Docker para Credenciales

### 3.1 Verificar que .gitignore excluye credenciales

Asegúrate de que `.gitignore` incluye:

```gitignore
# Credenciales y configuración local
.env.local
credentials/
*.json
```

### 3.2 Montar credenciales en Docker

Los Dockerfiles ya están configurados para montar el directorio `credentials/` como volumen de solo lectura.

## 🧪 Paso 4: Verificar Configuración

### 4.1 Test de autenticación

```bash
# Activar entorno virtual
source .venv/bin/activate

# Configurar variable de entorno
export GOOGLE_APPLICATION_CREDENTIALS="credentials/service-account-local.json"

# Test básico de autenticación
python -c "
from google.cloud import firestore
from google.cloud import bigquery
from google.cloud import storage
import vertexai

print('🔍 Verificando autenticación...')

# Test Firestore
try:
    db = firestore.Client(project='genai-385616')
    print('✅ Firestore: Autenticación OK')
except Exception as e:
    print(f'❌ Firestore: {e}')

# Test BigQuery
try:
    client = bigquery.Client(project='genai-385616')
    print('✅ BigQuery: Autenticación OK')
except Exception as e:
    print(f'❌ BigQuery: {e}')

# Test Cloud Storage
try:
    client = storage.Client(project='genai-385616')
    print('✅ Cloud Storage: Autenticación OK')
except Exception as e:
    print(f'❌ Cloud Storage: {e}')

# Test Vertex AI
try:
    vertexai.init(project='genai-385616', location='us-central1')
    print('✅ Vertex AI: Autenticación OK')
except Exception as e:
    print(f'❌ Vertex AI: {e}')

print('🎉 Verificación completada')
"
```

## 🚨 Solución de Problemas

### Error: "Could not automatically determine credentials"

**Causa**: Variable `GOOGLE_APPLICATION_CREDENTIALS` no configurada o archivo no encontrado.

**Solución**:
```bash
# Verificar que la variable está configurada
echo $GOOGLE_APPLICATION_CREDENTIALS

# Verificar que el archivo existe
ls -la credentials/service-account-local.json

# Reconfigurar si es necesario
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials/service-account-local.json"
```

### Error: "Permission denied" o "Insufficient permissions"

**Causa**: Service Account no tiene los permisos necesarios.

**Solución**:
```bash
# Verificar roles asignados
gcloud projects get-iam-policy genai-385616 \
    --flatten="bindings[].members" \
    --filter="bindings.members:corpchat-local-dev@genai-385616.iam.gserviceaccount.com" \
    --format="table(bindings.role)"

# Re-asignar roles si es necesario (ver comandos arriba)
```

### Error: "Project not found" o "Invalid project ID"

**Causa**: Project ID incorrecto o acceso denegado.

**Solución**:
```bash
# Verificar proyecto configurado
gcloud config get-value project

# Cambiar proyecto si es necesario
gcloud config set project genai-385616

# Verificar acceso al proyecto
gcloud projects describe genai-385616
```

### Error en Docker: "Credentials not found"

**Causa**: Volumen de credenciales no montado correctamente.

**Solución**:
```bash
# Verificar que docker-compose.yml monta el volumen
grep -A 10 -B 5 "credentials" docker-compose.yml

# Verificar que el archivo existe en el host
ls -la credentials/service-account-local.json

# Recrear contenedores
docker-compose down
docker-compose up -d
```

## 🔄 Mantenimiento

### Rotar credenciales

Las credenciales de Service Account deben rotarse periódicamente:

```bash
# Crear nueva key
gcloud iam service-accounts keys create credentials/service-account-local-new.json \
    --iam-account=corpchat-local-dev@genai-385616.iam.gserviceaccount.com

# Reemplazar archivo existente
mv credentials/service-account-local-new.json credentials/service-account-local.json

# Eliminar key antigua (opcional)
# gcloud iam service-accounts keys delete KEY_ID \
#     --iam-account=corpchat-local-dev@genai-385616.iam.gserviceaccount.com
```

### Limpiar credenciales

```bash
# Eliminar credenciales locales
rm -rf credentials/
rm .env.local

# Regenerar desde template
cp .env.local.template .env.local
# Reconfigurar variables según sea necesario
```

## 📚 Referencias

- [Google Cloud Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
- [IAM Roles](https://cloud.google.com/iam/docs/understanding-roles)
- [Local Development with Docker](https://cloud.google.com/docs/authentication/production)

## 🔐 Seguridad

### Buenas Prácticas

1. **Nunca commitar credenciales** al repositorio
2. **Usar .gitignore** para excluir archivos sensibles
3. **Rotar credenciales** periódicamente
4. **Principio de menor privilegio** en roles IAM
5. **Monitorear uso** de credenciales
6. **Eliminar credenciales** cuando no se necesiten

### Variables de Entorno Seguras

```bash
# En lugar de hardcodear en archivos
GOOGLE_CLOUD_PROJECT=genai-385616  # ✅ Correcto
PROJECT_ID=genai-385616            # ❌ Evitar

# Usar archivos de entorno
source .env.local                  # ✅ Correcto
export GOOGLE_CLOUD_PROJECT=...    # ✅ Correcto
```

---

**Última actualización**: 2025-10-19
**Versión**: 1.0
