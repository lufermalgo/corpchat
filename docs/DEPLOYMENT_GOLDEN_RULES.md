# Reglas de Oro para Deployment CorpChat

## 🎯 **REGLA FUNDAMENTAL**

**DESPUÉS DE CADA DEPLOYMENT, SIEMPRE VALIDAR QUE TODOS LOS SERVICIOS CLOUD RUN TENGAN ACCESO PÚBLICO Y ESTÉN OPERATIVOS.**

## 📋 **CHECKLIST OBLIGATORIO POST-DEPLOYMENT**

### 1. ✅ **Validación de Acceso Cloud Run**

```bash
# Ejecutar script de validación automática
./scripts/validate_cloud_run_access.sh
```

**Verificar que todos los servicios tengan:**
- ✅ Estado: `True` (activo)
- ✅ Permisos: `allUsers` con `roles/run.invoker`
- ✅ Conectividad: HTTP 200/404

### 2. ✅ **Servicios Críticos de CorpChat**

| Servicio | Descripción | URL | Acceso Requerido |
|----------|-------------|-----|------------------|
| `corpchat-gateway` | API Gateway OpenAI-compatible | `/v1/chat/completions` | Público |
| `corpchat-ingestor` | Procesador de documentos | `/extract/process` | Público |
| `corpchat-orchestrator` | ADK Multi-Agent | `/orchestrate` | Público |
| `corpchat-ui` | Open WebUI Interface | `/` | Público |

### 3. ✅ **Comandos de Corrección Rápida**

Si algún servicio no tiene acceso público:

```bash
# Corregir acceso público para cualquier servicio
gcloud run services add-iam-policy-binding [SERVICE_NAME] \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region=us-central1 \
  --project=genai-385616
```

## 🔧 **PROCESO DE DEPLOYMENT ESTÁNDAR**

### **Paso 1: Deploy de Servicios**

```bash
# Gateway
gcloud builds submit --config services/gateway/cloudbuild-simple.yaml

# Ingestor  
gcloud builds submit --config services/ingestor/cloudbuild-simple.yaml

# UI
gcloud builds submit --config services/ui/cloudbuild-simple.yaml
```

### **Paso 2: Validación Automática**

```bash
# Ejecutar validación completa
./scripts/post_deployment_validation.sh
```

### **Paso 3: Corrección si es Necesaria**

Si la validación falla, ejecutar:

```bash
# Corregir acceso a todos los servicios CorpChat
for service in corpchat-gateway corpchat-ingestor corpchat-orchestrator corpchat-ui; do
  gcloud run services add-iam-policy-binding $service \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --region=us-central1 \
    --project=genai-385616
done
```

## 🚨 **PROBLEMAS COMUNES Y SOLUCIONES**

### **Problema 1: Servicio No Accesible**

**Síntomas:**
- HTTP 403 Forbidden
- Error de autenticación

**Solución:**
```bash
gcloud run services add-iam-policy-binding [SERVICE_NAME] \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region=us-central1 \
  --project=genai-385616
```

### **Problema 2: Cold Starts**

**Síntomas:**
- Timeout en primera llamada
- Latencia alta inicial

**Solución:**
```bash
# Configurar min-instances para servicios críticos
gcloud run services update corpchat-gateway \
  --min-instances=1 \
  --region=us-central1 \
  --project=genai-385616
```

### **Problema 3: Variables de Entorno Perdidas**

**Síntomas:**
- Error 500 Internal Server Error
- Logs muestran variables faltantes

**Solución:**
- Verificar `cloudbuild-simple.yaml` tiene todas las variables
- Re-deploy usando `gcloud builds submit`

## 📊 **MÉTRICAS DE ÉXITO**

### **Validación Exitosa Debe Mostrar:**

```
🔍 VALIDACIÓN DE ACCESO CLOUD RUN - CORPCHAT
==============================================

📋 Estado de Servicios:
🔧 corpchat-gateway (Gateway API)
  ✅ Servicio: Activo
  ✅ Permisos: Público (allUsers)

🔧 corpchat-ingestor (Document Ingestor)  
  ✅ Servicio: Activo
  ✅ Permisos: Público (allUsers)

🔧 corpchat-orchestrator (ADK Orchestrator)
  ✅ Servicio: Activo
  ✅ Permisos: Público (allUsers)

🔧 corpchat-ui (Open WebUI Interface)
  ✅ Servicio: Activo
  ✅ Permisos: Público (allUsers)

🌐 Verificación de Conectividad:
🔗 Testing corpchat-gateway...
  ✅ Conectividad: OK (HTTP 200)

🔗 Testing corpchat-ingestor...
  ✅ Conectividad: OK (HTTP 200)

🔗 Testing corpchat-ui...
  ✅ Conectividad: OK (HTTP 200)

📊 RESUMEN DE VALIDACIÓN:
========================
Servicios Activos: 4/4
✅ TODOS LOS SERVICIOS ESTÁN ACTIVOS Y ACCESIBLES
```

## 🔄 **AUTOMATIZACIÓN RECOMENDADA**

### **Integrar en CI/CD Pipeline:**

```yaml
# .github/workflows/deploy.yml
- name: Deploy Services
  run: |
    gcloud builds submit --config services/gateway/cloudbuild-simple.yaml
    gcloud builds submit --config services/ingestor/cloudbuild-simple.yaml  
    gcloud builds submit --config services/ui/cloudbuild-simple.yaml

- name: Validate Deployment
  run: |
    ./scripts/post_deployment_validation.sh
```

### **Script de Deploy Completo:**

```bash
#!/bin/bash
# deploy_corpchat.sh

set -e

echo "🚀 DEPLOYING CORPCHAT..."

# Deploy servicios
echo "📦 Deploying Gateway..."
gcloud builds submit --config services/gateway/cloudbuild-simple.yaml

echo "📦 Deploying Ingestor..."
gcloud builds submit --config services/ingestor/cloudbuild-simple.yaml

echo "📦 Deploying UI..."
gcloud builds submit --config services/ui/cloudbuild-simple.yaml

# Validación obligatoria
echo "🔍 Validating deployment..."
./scripts/post_deployment_validation.sh

echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY"
```

## 🎯 **REGLA DE ORO RESUMIDA**

> **"NUNCA TERMINAR UN DEPLOYMENT SIN VALIDAR QUE TODOS LOS SERVICIOS CLOUD RUN TENGAN ACCESO PÚBLICO Y ESTÉN OPERATIVOS. SIEMPRE EJECUTAR `./scripts/post_deployment_validation.sh` DESPUÉS DE CADA DEPLOY."**

## 📞 **COMANDOS DE EMERGENCIA**

Si algo sale mal:

```bash
# 1. Verificar estado de todos los servicios
gcloud run services list --project=genai-385616 --region=us-central1

# 2. Corregir acceso público para todos
for service in corpchat-gateway corpchat-ingestor corpchat-orchestrator corpchat-ui; do
  gcloud run services add-iam-policy-binding $service \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --region=us-central1 \
    --project=genai-385616
done

# 3. Validar que todo funcione
./scripts/post_deployment_validation.sh
```
