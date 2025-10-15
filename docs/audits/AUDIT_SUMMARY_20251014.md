# Resumen Auditoría Proyecto genai-385616
**Fecha**: 14 de octubre 2025  
**Usuario**: fmaldonado@summan.com  
**Proyecto**: genai-385616 (GenAI)

---

## ✅ Estado: SEGURO PARA DEPLOYMENT

### Recursos CorpChat - Estado Actual

| Recurso | Tipo | Estado | Acción |
|---------|------|--------|--------|
| Cloud Run Services | `corpchat-*` | ❌ No existen | ✅ Crear |
| GCS Bucket | `corpchat-genai-385616-attachments` | ❌ No existe | ✅ Crear |
| Service Account | `corpchat-app` | ❌ No existe | ✅ Crear |
| Pub/Sub Topic | `attachments-finalized` | ❌ No existe | ✅ Crear |
| Secret | `corpchat-config` | ❌ No existe | ✅ Crear |
| Firestore | `(default)` | ✅ **EXISTE COMPARTIDA** | ⚠️ Usar prefijos `corpchat_` |

---

## 📊 Estado del Proyecto Compartido

### Recursos Existentes (Otros Proyectos)

- **Cloud Run Services**: 43 servicios activos
  - Ejemplos: bot, chatbot-backend, consulta-bq, demo-gen-ai, etc.
  - ✅ Ninguno con prefijo "corpchat"

- **GCS Buckets**: 78 buckets
  - Ejemplos: archivos_agentspace_summan, argos_cartillas, ces-poc, etc.
  - ✅ Ninguno con prefijo "corpchat"

- **Service Accounts**: 15 existentes
  - Incluye: agent-bigquery@genai-385616.iam.gserviceaccount.com
  - ✅ Ninguno con prefijo "corpchat"

- **Secrets**: 4 existentes
  - agent-bigquery-token, dialogflow-tool-sa, genai-vision-demo-api-secret, key_notion
  - ✅ Ninguno con prefijo "corpchat"

- **Firestore**: 1 base de datos compartida
  - Tipo: FIRESTORE_NATIVE
  - Ubicación: nam5
  - Creada: 2024-09-05
  - ⚠️ **COMPARTIDA** - No podemos listar colecciones (permisos)

- **Pub/Sub Topics**: 0 existentes
  - ✅ Podemos crear el nuestro sin conflictos

---

## 🔧 APIs Habilitadas

| API | Estado |
|-----|--------|
| Cloud Run | ✅ HABILITADO |
| Firestore | ✅ HABILITADO |
| Cloud Storage | ✅ HABILITADO |
| Vertex AI | ✅ HABILITADO |
| Secret Manager | ✅ HABILITADO |
| IAP | ❌ **DESHABILITADO** - Necesita habilitarse |

---

## ⚠️ Riesgos Identificados

### 1. Firestore Compartida (MITIGADO)

**Riesgo**: Colisión de nombres de colecciones con otros proyectos

**Mitigación Implementada**: ✅
- Prefijo `corpchat_` en todas las colecciones
- Código actualizado en `services/agents/shared/firestore_client.py`
- Constante `COLLECTION_PREFIX = "corpchat_"`

**Colecciones que usaremos**:
- `corpchat_users`
- `corpchat_chats`
- `corpchat_messages` (subcolección)
- `corpchat_attachments`
- `corpchat_chunks` (subcolección)
- `corpchat_knowledge_base`
- `corpchat_contents` (subcolección)

### 2. Proyecto Muy Activo (BAJO RIESGO)

**Observación**: 43 servicios Cloud Run activos de otros compañeros

**Mitigación**: ✅
- Prefijo `corpchat-` en todos nuestros servicios
- Labels obligatorios: `team=corpchat`, `env=dev|stage|prod`
- Naming convention consistente

### 3. IAP No Configurado (PENDIENTE)

**Acción requerida**: Habilitar IAP y configurar OAuth 2.0 Client ID

---

## 📋 Plan de Acción - Setup GCP

### Paso 1: Habilitar Servicios (Incluye IAP)

```bash
cd /Users/lufermalgo/Proyectos/CorpChat/infra/scripts
./enable_services.sh
```

**Servicios a habilitar**:
- ✅ run.googleapis.com (ya habilitado)
- ✅ firestore.googleapis.com (ya habilitado)
- ✅ storage.googleapis.com (ya habilitado)
- ✅ aiplatform.googleapis.com (ya habilitado)
- ✅ secretmanager.googleapis.com (ya habilitado)
- ❌ **iap.googleapis.com** (PENDIENTE)
- cloudbuild.googleapis.com
- cloudscheduler.googleapis.com
- pubsub.googleapis.com
- monitoring.googleapis.com
- logging.googleapis.com

### Paso 2: Ejecutar Setup Principal

```bash
cd /Users/lufermalgo/Proyectos/CorpChat/infra/scripts
./setup_gcp.sh
```

**Recursos que creará**:
1. ✅ Firestore: Detectará que existe, NO intentará crear
2. ✅ Bucket GCS: `corpchat-genai-385616-attachments` con lifecycle policies
3. ✅ Service Account: `corpchat-app@genai-385616.iam.gserviceaccount.com`
4. ✅ IAM Bindings: roles/datastore.user, roles/storage.objectAdmin, roles/secretmanager.secretAccessor, roles/aiplatform.user
5. ✅ Pub/Sub Topic: `attachments-finalized`
6. ✅ GCS Notification: Bucket → Pub/Sub
7. ✅ Secret: `corpchat-config`

### Paso 3: Configurar IAP (Manual)

1. Ir a GCP Console → Security → Identity-Aware Proxy
2. Habilitar API si no está habilitada
3. Configurar OAuth consent screen
4. Crear OAuth 2.0 Client ID
5. Configurar Backend Services para Cloud Run
6. Agregar usuarios/grupos autorizados

---

## 🔒 Medidas de Seguridad Implementadas

1. ✅ Script de auditoría (`audit_gcp.sh`) - Solo lectura
2. ✅ Confirmaciones obligatorias en `setup_gcp.sh`
3. ✅ Soporte para `--dry-run` mode
4. ✅ Prefijos en TODOS los recursos
5. ✅ Labels para identificación
6. ✅ Verificación de recursos existentes antes de crear
7. ✅ Documentación de seguridad (`SHARED_PROJECT_SAFETY.md`)

---

## 🎯 Recomendaciones Finales

### Para Desarrollo

✅ **PROCEDER con setup en genai-385616**

**Justificación**:
- No hay colisiones de nombres
- Mitigaciones implementadas
- Proyecto corporativo con recursos adecuados
- Firestore compartida manejada con prefijos

### Para Producción (Futuro)

**Considerar**:
- Proyecto GCP dedicado para producción
- Firestore dedicada
- Budgets y alertas específicos
- Separación completa de recursos

---

## 📞 Contactos

**Proyecto**: genai-385616  
**Organización**: Summan (folder ID: 495366155012)  
**Usuario**: fmaldonado@summan.com  
**Equipo**: GenAI Team

---

## ✅ Conclusión

**Estado**: ✅ VERDE - Seguro para proceder  
**Confianza**: ALTA  
**Próximo paso**: Ejecutar `./infra/scripts/enable_services.sh`

**Validaciones completadas**:
- [x] Autenticación con cuenta corporativa
- [x] Acceso al proyecto verificado
- [x] Auditoría de recursos existentes
- [x] Verificación de colisiones (ninguna encontrada)
- [x] Mitigaciones implementadas
- [x] Documentación de seguridad creada

**LISTO PARA DEPLOYMENT** 🚀

