# Guía de Deployment - CorpChat MVP

## Prerrequisitos

### Herramientas Locales

- Python 3.13+
- Docker
- `gcloud` CLI configurado
- Acceso al proyecto GCP `genai-385616`
- Google Workspace account con permisos IAP

### Permisos GCP Requeridos

```
roles/run.admin
roles/iap.admin
roles/iam.serviceAccountAdmin
roles/storage.admin
roles/datastore.owner
roles/secretmanager.admin
roles/billing.costsManager
roles/cloudbuild.builds.editor
```

## Setup Inicial (Una Sola Vez)

### 1. Clonar Repositorio

```bash
git clone https://github.com/lufermalgo/corpchat.git
cd corpchat
```

### 2. Clonar Referencias

```bash
mkdir -p references
cd references
git clone https://github.com/google/adk-python.git adk-python-ref
git clone https://github.com/open-webui/open-webui.git open-webui-base
git clone https://github.com/open-webui/docs.git open-webui-docs
cd ..
```

### 3. Configurar GCP

```bash
# Configurar proyecto
export PROJECT_ID=genai-385616
export REGION=us-central1

gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# Ejecutar script de setup
cd infra/scripts
./setup_gcp.sh
cd ../..
```

Este script crea:
- Firestore database
- Bucket GCS con lifecycle policies
- Service account con permisos
- Pub/Sub topics
- Secrets

### 4. Configurar IAP

**En GCP Console:**

1. Navegar a **Security → Identity-Aware Proxy**
2. Click en **Configure Consent Screen**
3. Seleccionar **Internal** (para Google Workspace)
4. Completar información de la app:
   - App name: `CorpChat`
   - User support email: tu email
   - Developer contact: tu email
5. Click **Create**

6. Ir a **APIs & Services → Credentials**
7. Click **Create Credentials → OAuth 2.0 Client ID**
8. Application type: **Web application**
9. Name: `CorpChat IAP Client`
10. Authorized redirect URIs: `https://iap.googleapis.com/v1/oauth/clientIds/<CLIENT_ID>:handleRedirect`
11. Click **Create**
12. **Guardar Client ID y Client Secret**

### 5. Configurar Variables de Entorno

```bash
cp env.template .env
# Editar .env con tus valores:
#   - IAP_CLIENT_ID
#   - IAP_CLIENT_SECRET
```

### 6. Crear Entornos Virtuales

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

## Deployment

### Orden de Deployment

1. Gateway (primero, ya que otros dependen)
2. Tool Servers
3. Ingestor
4. Agents (Orchestrator + Specialists)
5. Open WebUI

### 1. Deploy Gateway

```bash
cd services/gateway

# Build y push imagen
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_ENVIRONMENT=dev,SHORT_SHA=$(git rev-parse --short HEAD)

# Verificar deployment
gcloud run services describe corpchat-gateway --region=us-central1
```

**Endpoint esperado**: `https://corpchat-gateway-<hash>-uc.a.run.app`

### 2. Deploy Tool Servers

```bash
# Docs Tool
cd services/tools/docs_tool
gcloud builds submit --config cloudbuild.yaml

# Sheets Tool
cd ../sheets_tool
gcloud builds submit --config cloudbuild.yaml

cd ../../..
```

### 3. Deploy Ingestor

```bash
cd services/ingestor
gcloud builds submit --config cloudbuild.yaml
cd ../..
```

### 4. Deploy Agents

**Orchestrator:**
```bash
cd services/agents/orchestrator
gcloud builds submit --config cloudbuild.yaml
cd ../../..
```

**Specialists:**
```bash
# Conocimiento Empresa
cd services/agents/specialists/conocimiento_empresa
gcloud builds submit --config cloudbuild.yaml

# Estado Técnico
cd ../estado_tecnico
gcloud builds submit --config cloudbuild.yaml

# Productos & Propuestas
cd ../productos_propuestas
gcloud builds submit --config cloudbuild.yaml

cd ../../../..
```

### 5. Deploy Open WebUI

```bash
cd services/ui

# Build imagen con branding
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_APP_TITLE=CorpChat,SHORT_SHA=$(git rev-parse --short HEAD)

cd ../..
```

### 6. Configurar IAP para Open WebUI

**En GCP Console:**

1. Navegar a **Network Services → Load Balancing**
2. Click en el load balancer creado automáticamente para `corpchat-ui`
3. Click **Edit**
4. Ir a **Backend Configuration**
5. Click en el backend service
6. Habilitar **Cloud IAP**
7. Seleccionar el OAuth Client ID creado anteriormente
8. Click **Save**

9. Ir a **Security → Identity-Aware Proxy**
10. Encontrar `corpchat-ui` en la lista
11. Marcar checkbox y click **Add Principal**
12. Agregar usuarios/grupos autorizados:
    - Principal: `user:email@domain.com` o `group:team@domain.com`
    - Role: `IAP-secured Web App User`
13. Click **Save**

### 7. Verificar Deployment

```bash
# Listar servicios desplegados
gcloud run services list --region=us-central1

# Obtener URL de Open WebUI
WEBUI_URL=$(gcloud run services describe corpchat-ui \
  --region=us-central1 \
  --format='value(status.url)')

echo "Open WebUI: $WEBUI_URL"
```

Abrir `$WEBUI_URL` en el navegador. Deberías ver:
1. Redirect a Google login
2. Selección de cuenta
3. Pantalla de Open WebUI con branding "CorpChat"

## Testing Post-Deployment

### 1. Health Checks

```bash
# Gateway
curl https://corpchat-gateway-<hash>-uc.a.run.app/health

# Orchestrator
curl https://corpchat-orchestrator-<hash>-uc.a.run.app/health

# Ingestor
curl https://corpchat-ingestor-<hash>-uc.a.run.app/health
```

### 2. Test E2E Manual

1. **Login**: Acceder a Open WebUI con cuenta corporativa
2. **Chat básico**: Enviar mensaje "Hola"
3. **Adjunto**: Subir un PDF simple y preguntar sobre su contenido
4. **Especialista**: Hacer pregunta que requiera un especialista

### 3. Tests Automatizados

```bash
cd tests/e2e
source ../../services/gateway/.venv/bin/activate
pytest test_full_flow.py -v
```

## Configuración FinOps

### Budgets

```bash
# Dev budget
gcloud beta billing budgets create \
  --billing-account=<BILLING_ACCOUNT_ID> \
  --display-name="CorpChat Dev" \
  --budget-amount=50 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100

# Stage budget
gcloud beta billing budgets create \
  --billing-account=<BILLING_ACCOUNT_ID> \
  --display-name="CorpChat Stage" \
  --budget-amount=100 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100

# Prod budget
gcloud beta billing budgets create \
  --billing-account=<BILLING_ACCOUNT_ID> \
  --display-name="CorpChat Prod" \
  --budget-amount=500 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100
```

### Auto-apagado Dev/Stage

```bash
# Cloud Scheduler: apagar dev cada noche
gcloud scheduler jobs create http dev-shutdown \
  --schedule="0 19 * * 1-5" \
  --time-zone="America/Mexico_City" \
  --uri="https://run.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/services/corpchat-ui" \
  --http-method=PATCH \
  --message-body='{"spec":{"template":{"metadata":{"annotations":{"autoscaling.knative.dev/minScale":"0","autoscaling.knative.dev/maxScale":"0"}}}}}' \
  --oidc-service-account-email="${SERVICE_ACCOUNT}"

# Cloud Scheduler: encender dev cada mañana
gcloud scheduler jobs create http dev-wakeup \
  --schedule="0 8 * * 1-5" \
  --time-zone="America/Mexico_City" \
  --uri="https://run.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/services/corpchat-ui" \
  --http-method=PATCH \
  --message-body='{"spec":{"template":{"metadata":{"annotations":{"autoscaling.knative.dev/minScale":"0","autoscaling.knative.dev/maxScale":"5"}}}}}' \
  --oidc-service-account-email="${SERVICE_ACCOUNT}"
```

### Exportar Billing a BigQuery

```bash
# Crear dataset
bq mk --dataset \
  --location=US \
  --description="CorpChat Billing Export" \
  ${PROJECT_ID}:billing_export

# Configurar export (en Console):
# Billing → Billing Export → BigQuery Export → Enable
```

## Monitoreo

### Dashboards

1. Navegar a **Monitoring → Dashboards**
2. Click **Create Dashboard**
3. Nombre: `CorpChat Cost-to-Serve`

**Widgets a agregar**:

- **Costo por Chat**:
  ```
  sum(rate(billing_export.cost[1h]))
  / sum(rate(run_googleapis_com_request_count{service_name="corpchat-orchestrator"}[1h]))
  ```

- **Tokens por Request (p95)**:
  ```
  histogram_quantile(0.95,
    sum(rate(custom_googleapis_com_tokens_used_bucket[5m])) by (le)
  )
  ```

- **Latencia Gateway**:
  ```
  histogram_quantile(0.95,
    sum(rate(run_googleapis_com_request_latencies_bucket{service_name="corpchat-gateway"}[5m])) by (le)
  )
  ```

### Alertas

```bash
# Alerta: Spend rate > 110%
gcloud alpha monitoring policies create \
  --notification-channels=<CHANNEL_ID> \
  --display-name="CorpChat Spend Rate Alert" \
  --condition-display-name="Spend > 110% budget" \
  --condition-threshold-value=1.1 \
  --condition-threshold-duration=3600s
```

## Rollback

### Rollback de un Servicio

```bash
# Listar revisiones
gcloud run revisions list --service=corpchat-gateway --region=us-central1

# Rollback a revisión anterior
gcloud run services update-traffic corpchat-gateway \
  --to-revisions=corpchat-gateway-00002-xyz=100 \
  --region=us-central1
```

### Rollback Total

```bash
# Script para rollback de todos los servicios
for service in corpchat-ui corpchat-gateway corpchat-orchestrator corpchat-ingestor; do
  echo "Rolling back $service..."
  PREVIOUS=$(gcloud run revisions list \
    --service=$service \
    --region=us-central1 \
    --format='value(metadata.name)' \
    --sort-by=~metadata.creationTimestamp \
    --limit=2 | tail -1)
  
  gcloud run services update-traffic $service \
    --to-revisions=$PREVIOUS=100 \
    --region=us-central1
done
```

## Troubleshooting

### Logs

```bash
# Ver logs de un servicio
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=corpchat-gateway" \
  --limit=50 \
  --format=json

# Logs en tiempo real
gcloud alpha run services logs tail corpchat-gateway --region=us-central1
```

### Problemas Comunes

#### 1. IAP no funciona

**Síntoma**: Redirect loop o 403

**Solución**:
- Verificar que `WEBUI_AUTH_PROVIDER=trusted_header` en Open WebUI
- Confirmar que el OAuth Client ID es correcto
- Revisar IAM bindings del backend service

#### 2. Gateway no se conecta a Vertex AI

**Síntoma**: 403 Permission Denied

**Solución**:
```bash
# Verificar permisos
gcloud projects get-iam-policy genai-385616 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:corpchat-app@*"

# Agregar rol si falta
gcloud projects add-iam-policy-binding genai-385616 \
  --member=serviceAccount:corpchat-app@genai-385616.iam.gserviceaccount.com \
  --role=roles/aiplatform.user
```

#### 3. Ingestor no procesa adjuntos

**Síntoma**: Archivos quedan en estado "processing"

**Solución**:
- Verificar notificaciones GCS:
  ```bash
  gsutil notification list gs://corpchat-genai-385616-attachments
  ```
- Revisar logs del ingestor
- Verificar Pub/Sub subscription está activa

#### 4. Costos inesperados

**Síntoma**: Gasto mayor al esperado

**Acciones**:
1. Revisar dashboard de billing
2. Verificar `min_instances=0` en todos los servicios
3. Revisar logs de tokens consumidos
4. Activar guardrails inmediatamente

## Actualizaciones

### Actualizar un Servicio

```bash
cd services/<servicio>

# Hacer cambios en código

# Build y deploy
gcloud builds submit --config cloudbuild.yaml

# Verificar nueva revisión
gcloud run revisions list --service=<servicio> --region=us-central1

# Si hay problemas, rollback (ver sección Rollback)
```

### Actualizar Configuración

```bash
# Actualizar variables de entorno
gcloud run services update corpchat-gateway \
  --update-env-vars KEY=value \
  --region=us-central1

# Actualizar límites
gcloud run services update corpchat-gateway \
  --max-instances=10 \
  --region=us-central1
```

## Backup y Recovery

### Backup Firestore

```bash
# Export manual
gcloud firestore export gs://corpchat-genai-385616-backups/$(date +%Y%m%d)

# Scheduled exports (Cloud Scheduler)
# TODO: Implementar
```

### Backup Configuración

```bash
# Export configuración de servicios
for service in corpchat-ui corpchat-gateway corpchat-orchestrator corpchat-ingestor; do
  gcloud run services describe $service \
    --region=us-central1 \
    --format=yaml > backups/${service}-config-$(date +%Y%m%d).yaml
done
```

## Próximos Pasos

1. Implementar pipeline CI/CD completo en Cloud Build
2. Configurar entornos stage y prod
3. Implementar tests de carga
4. Configurar disaster recovery
5. Documentar runbooks operacionales

## Referencias

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [IAP Documentation](https://cloud.google.com/iap/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)

