# CorpChat Terraform Modules - Multi-Cliente

Módulos de Terraform para desplegar CorpChat de manera replicable para múltiples clientes.

## Estructura

```
terraform/
├── modules/
│   └── corpchat/              # Módulo principal reutilizable
│       ├── main.tf            # Recursos GCP
│       ├── variables.tf       # Variables configurables
│       └── outputs.tf         # Outputs del módulo
└── environments/
    └── example-client/        # Ejemplo de deployment
        ├── main.tf            # Configuración del cliente
        ├── variables.tf       # Variables del cliente
        ├── outputs.tf         # Outputs del cliente
        └── terraform.tfvars.example  # Ejemplo de valores
```

## Recursos Desplegados

El módulo `corpchat` despliega:

### Compute
- **4 Cloud Run Services**:
  - Gateway (OpenAI-compatible API)
  - UI (Open WebUI)
  - Orchestrator (ADK Multi-Agent)
  - Ingestor (Document Processing Pipeline)

### Storage
- **GCS Bucket** para attachments con lifecycle policies
- **BigQuery Dataset** con tabla de embeddings particionada
- **Firestore** (existente, con prefijos por cliente)

### IAM
- **Service Account** dedicada por cliente
- **IAM Bindings** necesarios (Vertex AI, BigQuery, GCS, Firestore)
- **Cloud Run IAM** para invokers autenticados

### Features
- Auto-scaling (min/max instances configurables)
- FinOps ready (min_instances=0 por defecto)
- Labels consistentes para cost tracking
- Lifecycle policies en GCS
- Particionamiento y clustering en BigQuery

## Desplegar para un Nuevo Cliente

### 1. Preparar Imágenes

Primero, construir y pushear las imágenes de los servicios a Artifact Registry:

```bash
# Desde el root del proyecto
cd services/gateway
gcloud builds submit --config=cloudbuild.yaml --project=genai-385616

cd ../ui
gcloud builds submit --config=cloudbuild.yaml --project=genai-385616

cd ../agents/orchestrator
gcloud builds submit --config=cloudbuild.yaml --project=genai-385616

cd ../../ingestor
gcloud builds submit --config=cloudbuild.yaml --project=genai-385616
```

### 2. Crear Directorio del Cliente

```bash
cd infra/terraform/environments
cp -r example-client nuevo-cliente
cd nuevo-cliente
```

### 3. Configurar Variables

Copiar y editar `terraform.tfvars`:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Editar `terraform.tfvars`:

```hcl
project_id   = "proyecto-gcp-del-cliente"
region       = "us-central1"
client_name  = "nuevo-cliente"  # lowercase, sin espacios
environment  = "prod"           # dev, staging, o prod

# Container images (usar las mismas para todos los clientes)
gateway_image      = "us-central1-docker.pkg.dev/genai-385616/corpchat/corpchat-gateway:latest"
ui_image           = "us-central1-docker.pkg.dev/genai-385616/corpchat/corpchat-ui:latest"
orchestrator_image = "us-central1-docker.pkg.dev/genai-385616/corpchat/corpchat-orchestrator:latest"
ingestor_image     = "us-central1-docker.pkg.dev/genai-385616/corpchat/corpchat-ingestor:latest"
```

### 4. Habilitar APIs de GCP

```bash
gcloud services enable \
  run.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  artifactregistry.googleapis.com \
  --project=proyecto-gcp-del-cliente
```

### 5. Inicializar Terraform

```bash
terraform init
```

### 6. Validar Configuración

```bash
terraform plan
```

Revisar que todos los recursos se crearán correctamente.

### 7. Aplicar Deployment

```bash
terraform apply
```

Confirmar con `yes` cuando se solicite.

### 8. Obtener URLs de Servicios

```bash
terraform output
```

Ejemplo de output:

```
deployment_summary = {
  "client" = "nuevo-cliente"
  "environment" = "prod"
  "project" = "proyecto-gcp-del-cliente"
  "region" = "us-central1"
  "services" = {
    "gateway" = "https://nuevo-cliente-corpchat-gateway-xxx.run.app"
    "ingestor" = "https://nuevo-cliente-corpchat-ingestor-xxx.run.app"
    "orchestrator" = "https://nuevo-cliente-corpchat-orchestrator-xxx.run.app"
    "ui" = "https://nuevo-cliente-corpchat-ui-xxx.run.app"
  }
  "storage" = {
    "attachments_bucket" = "nuevo-cliente-corpchat-proyecto-gcp-del-cliente-attachments"
    "bigquery_dataset" = "nuevo_cliente_corpchat"
  }
}
```

## Variables Configurables

### Básicas
- `project_id`: GCP Project ID
- `region`: Región de GCP (default: us-central1)
- `client_name`: Nombre del cliente (lowercase)
- `environment`: dev, staging, o prod

### Compute
- `gateway_cpu/memory`: Recursos para Gateway (default: 1 CPU, 1Gi)
- `ui_cpu/memory`: Recursos para UI (default: 1 CPU, 512Mi)
- `orchestrator_cpu/memory`: Recursos para Orchestrator (default: 1 CPU, 1Gi)
- `ingestor_cpu/memory`: Recursos para Ingestor (default: 2 CPU, 2Gi)

### Scaling
- `min_instances`: Instancias mínimas (default: 0 para FinOps)
- `max_instances`: Instancias máximas (default: 10)

### Storage
- `attachment_bucket_lifecycle_days`: Días antes de Nearline (default: 30)
- `attachment_bucket_deletion_days`: Días antes de eliminar (default: 0 = nunca)

### BigQuery
- `bigquery_dataset_location`: Ubicación del dataset (default: US)
- `embedding_dimensions`: Dimensiones de embeddings (default: 768)

## Gestión de Estado

### Backend Local (Default)

Por defecto, el estado se guarda en `terraform.tfstate` localmente.

### Backend Remoto (Recomendado para Producción)

Crear bucket para estado:

```bash
gsutil mb -p genai-385616 -l us-central1 gs://terraform-state-corpchat
gsutil versioning set on gs://terraform-state-corpchat
```

Descomentar en `main.tf`:

```hcl
backend "gcs" {
  bucket = "terraform-state-corpchat"
  prefix = "clients/nuevo-cliente"
}
```

Migrar estado:

```bash
terraform init -migrate-state
```

## Actualizar Deployment

### Actualizar Imágenes

1. Construir nuevas imágenes con nuevo tag
2. Actualizar `terraform.tfvars` con nuevos tags
3. Aplicar:

```bash
terraform apply
```

### Actualizar Recursos

1. Modificar variables en `terraform.tfvars`
2. Aplicar:

```bash
terraform plan  # Revisar cambios
terraform apply
```

## Eliminar Deployment

**⚠️ CUIDADO**: Esto eliminará todos los recursos del cliente.

```bash
terraform destroy
```

## Cost Optimization

### FinOps Features Incluidas

1. **Auto-scaling a cero**: `min_instances = 0`
2. **Lifecycle policies**: GCS Nearline después de 30 días
3. **Partitioning**: BigQuery particionado por día
4. **Labels**: Todos los recursos etiquetados para cost tracking

### Monitoring de Costos

```bash
# Ver costos por label
gcloud billing projects describe PROJECT_ID \
  --format="table(costCenter, cost)"
```

## Troubleshooting

### Error: APIs no habilitadas

```bash
gcloud services list --enabled --project=PROJECT_ID
```

Habilitar APIs faltantes con `gcloud services enable`.

### Error: Permisos insuficientes

Verificar permisos del usuario/service account:

```bash
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)"
```

### Error: Imágenes no encontradas

Verificar que las imágenes existen en Artifact Registry:

```bash
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/genai-385616/corpchat
```

## Mejores Prácticas

1. **Un directorio por cliente** en `environments/`
2. **Backend remoto** para producción
3. **Versionado de imágenes** (no usar `:latest` en prod)
4. **Labels consistentes** para cost tracking
5. **Min instances = 0** para dev/staging
6. **Terraform workspace** para múltiples ambientes del mismo cliente

## Soporte

Para problemas o preguntas:
- Revisar logs: `gcloud logging read`
- Health checks: `./infra/scripts/health_check_all_services.sh`
- Documentación: `docs/`

---

**Última actualización**: 15 Octubre 2025

