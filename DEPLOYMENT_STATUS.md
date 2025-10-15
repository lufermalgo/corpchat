# CorpChat - Estado del Deployment

**Fecha**: 2025-10-15  
**Proyecto GCP**: `genai-385616`  
**Región**: `us-central1`

---

## ✅ Deployments Exitosos (2/3)

### 1. **Model Gateway** ✅
**Servicio**: `corpchat-gateway`  
**URL interna**: https://corpchat-gateway-[hash]-uc.a.run.app  
**Tiempo de deploy**: 2m 37s  
**Imagen**: `us-central1-docker.pkg.dev/genai-385616/corpchat/corpchat-gateway:39ff304`  
**Estado**: **DEPLOYED & RUNNING**

**Características**:
- Endpoint `/v1/chat/completions` (OpenAI-compatible)
- Proxy a Vertex AI Gemini 2.5 Flash
- Autenticación via IAP
- Logging estructurado
- FinOps: `min_instances=0`, `max_instances=5`, `512Mi` RAM

---

### 2. **Open WebUI** ✅
**Servicio**: `corpchat-ui`  
**URL pública**: https://corpchat-ui-[hash]-uc.a.run.app  
**Tiempo de deploy**: 3m 55s  
**Imagen**: `us-central1-docker.pkg.dev/genai-385616/corpchat/corpchat-ui:89bed39`  
**Estado**: **DEPLOYED & RUNNING**

**Características**:
- Basado en Open WebUI v0.6.32
- Branding basic (via ENV vars: `APP_TITLE=CorpChat`)
- Autenticación preparada para IAP (`WEBUI_AUTH_PROVIDER=trusted_header`)
- FinOps: `min_instances=0`, `max_instances=5`, `1Gi` RAM

**Nota**: Branding avanzado (CSS custom, favicon) se implementará en fase posterior.

---

### 3. **Orchestrator** ⏸️ (En debugging)
**Servicio**: `corpchat-orchestrator`  
**Imagen**: `us-central1-docker.pkg.dev/genai-385616/corpchat/corpchat-orchestrator:39cbe65`  
**Estado**: **BUILD OK, RUNTIME ERROR**

**Problema**:
```
ERROR: The user-provided container failed to start and listen on the port 
defined provided by the PORT=8080 environment variable within the allocated timeout.
```

**Logs URL**:
https://console.cloud.google.com/logs/viewer?project=genai-385616&resource=cloud_run_revision/service_name/corpchat-orchestrator/revision_name=corpchat-orchestrator-00002-v7j

**Causa probable**:
- Error de import en Python al inicializar Vertex AI
- Falta alguna dependencia de Google Cloud
- Error en inicialización de Firestore

**Implementación**:
- Orchestrator MVP sin ADK (usando `google-generativeai` directamente)
- Vertex AI Gemini 2.5 Flash
- Firestore para sesiones y historial
- Endpoints: `/chat`, `/health`, `/chats/{chat_id}/history`

---

## 🔧 Infraestructura GCP Configurada

### **Artifact Registry** ✅
- **Repositorio**: `corpchat`
- **Formato**: Docker
- **Ubicación**: `us-central1`
- **Imágenes**: 3 (gateway, ui, orchestrator)

### **IAP OAuth** ✅
- **OAuth Client ID**: `CorpChat IAP Client`
- **Secrets**:
  - `iap-oauth-client-id` (Secret Manager)
  - `iap-oauth-client-secret` (Secret Manager)

### **GCS Bucket** ✅
- **Bucket**: `corpchat-genai-385616-attachments`
- **Lifecycle**: 30 días
- **Notificaciones**: Pub/Sub topic `attachments-finalized`

### **Service Account** ✅
- **SA**: `corpchat-app@genai-385616.iam.gserviceaccount.com`
- **Roles**:
  - `roles/datastore.user`
  - `roles/storage.objectAdmin`
  - `roles/secretmanager.secretAccessor`
  - `roles/aiplatform.user`

### **Firestore** ✅
- **Modo**: Native
- **Prefijo**: `corpchat_` (para evitar colisiones)
- **Colecciones planeadas**: `users`, `chats`, `messages`, `attachments`, `chunks`

### **BigQuery Vector Store** (Pendiente)
- **Dataset**: `corpchat` (NO creado aún)
- **Tabla**: `embeddings` (NO creada aún)
- **Script**: `infra/scripts/setup_bigquery_vector_store.sh`

---

## 🚀 Próximos Pasos

### **Inmediato** (10-15 min)
1. **Debug Orchestrator**:
   ```bash
   # Ver logs en tiempo real
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=corpchat-orchestrator" \
     --project=genai-385616 \
     --limit=50 \
     --format=json
   ```

2. **Verificar servicios deployados**:
   ```bash
   gcloud run services list --project=genai-385616 --region=us-central1
   ```

3. **Obtener URLs**:
   ```bash
   # Gateway
   gcloud run services describe corpchat-gateway --region=us-central1 --project=genai-385616 --format="value(status.url)"
   
   # UI
   gcloud run services describe corpchat-ui --region=us-central1 --project=genai-385616 --format="value(status.url)"
   ```

---

### **Corto plazo** (1-2 horas)
1. ✅ **Setup BigQuery Vector Store**:
   ```bash
   chmod +x infra/scripts/setup_bigquery_vector_store.sh
   ./infra/scripts/setup_bigquery_vector_store.sh
   ```

2. 🔧 **Arreglar Orchestrator**: 
   - Revisar logs de Cloud Run
   - Simplificar inicialización si es necesario
   - Probar localmente con Docker
   - Re-deploy con fixes

3. 🔒 **Configurar IAP en UI**:
   ```bash
   gcloud iap web enable \
     --resource-type=backend-services \
     --service=corpchat-ui \
     --oauth2-client-id=[CLIENT_ID] \
     --oauth2-client-secret=[CLIENT_SECRET]
   ```

---

### **Mediano plazo** (1-2 días)
1. **Implementar Ingestor de Documentos**
2. **Implementar Tool Servers** (Docs Tool, Sheets Tool)
3. **Tests E2E básicos**
4. **Configurar FinOps**: Budgets, alertas, quotas

---

## 📊 Costos Estimados

### **Servicios Deployed** (min_instances=0)
- **Gateway**: ~$0/hora (idle), ~$0.10/hora (activo)
- **UI**: ~$0/hora (idle), ~$0.15/hora (activo)
- **Orchestrator**: (pendiente deployment)

### **Otros Recursos**
- **Artifact Registry**: ~$0.10/GB/mes (storage)
- **Secret Manager**: ~$0.06/secret/mes
- **Firestore**: Pay-per-use (reads/writes)
- **Vertex AI**: Pay-per-token (Gemini 2.5 Flash: ~$0.0001/1K tokens)

**Estimado mensual (uso ligero)**: **$10-30 USD**

---

## 🐛 Troubleshooting

### **Orchestrator no inicia**
```bash
# Ver logs detallados
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=corpchat-orchestrator" \
  --project=genai-385616 \
  --limit=100 \
  --format="table(timestamp, severity, textPayload)"

# Verificar imagen
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/genai-385616/corpchat/corpchat-orchestrator
```

### **IAP no funciona**
1. Verificar que el OAuth Client ID esté configurado correctamente
2. Verificar que los dominios autorizados incluyan `*.run.app`
3. Verificar que el service account tenga permisos

### **UI no carga**
1. Verificar que el servicio esté running: `gcloud run services describe corpchat-ui ...`
2. Verificar logs: `gcloud logging read "resource.labels.service_name=corpchat-ui" ...`
3. Verificar que no haya errores de timeout (aumentar con `--timeout=300s`)

---

## 📝 Documentación Relacionada

- `NEXT_STEPS_MANUAL.md` - Roadmap completo
- `GCP_SETUP_COMPLETE.md` - Estado de infraestructura
- `VECTOR_STORE_SETUP_COMPLETE.md` - BigQuery vector store
- `docs/deployment.md` - Guía de deployment
- `docs/IAP_OAUTH_SETUP_GUIDE.md` - Setup IAP

---

## ✅ Checklist de Validación

- [x] Proyecto GCP `genai-385616` configurado
- [x] APIs habilitadas
- [x] Service Account creada
- [x] Artifact Registry creado
- [x] Gateway deployed
- [x] UI deployed
- [x] OAuth configurado
- [ ] Orchestrator deployed
- [ ] BigQuery Vector Store creado
- [ ] IAP habilitado en UI
- [ ] Tests E2E ejecutados

---

**Última actualización**: 2025-10-15 02:12:00 UTC  
**Commit**: `39cbe65`  
**Branch**: `main`

