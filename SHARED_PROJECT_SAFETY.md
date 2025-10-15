# Seguridad en Proyecto GCP Compartido

**⚠️ ADVERTENCIA CRÍTICA**: El proyecto `genai-385616` es **compartido** con otros compañeros y contiene proyectos existentes.

---

## 🚨 Riesgos Identificados

1. **Firestore Compartido**: Si existe una base de datos Firestore, es compartida por todos
2. **Colisiones de Nombres**: Recursos con el mismo nombre se sobrescribirán
3. **Modificación Accidental**: Scripts pueden modificar recursos de otros proyectos
4. **Pérdida de Datos**: Eliminar/modificar colecciones puede afectar otros sistemas

---

## ✅ Medidas de Seguridad Implementadas

### 1. Script de Auditoría (EJECUTAR PRIMERO)

```bash
cd /Users/lufermalgo/Proyectos/CorpChat/infra/scripts
./audit_gcp.sh
```

**Este script:**
- ✅ **SOLO LECTURA** - No modifica nada
- Revisa servicios Cloud Run existentes
- Verifica si Firestore ya existe
- Lista buckets GCS
- Identifica Service Accounts
- Detecta colisiones potenciales
- Genera reporte de seguridad

**NUNCA ejecutar `setup_gcp.sh` sin antes ejecutar `audit_gcp.sh`**

### 2. Prefijos en Recursos

Todos los recursos usan prefijo `corpchat-` para evitar colisiones:

| Recurso | Nombre | Status |
|---------|--------|--------|
| Bucket GCS | `corpchat-genai-385616-attachments` | ✅ Con prefijo |
| Service Account | `corpchat-app` | ✅ Con prefijo |
| Cloud Run Services | `corpchat-ui`, `corpchat-gateway`, etc. | ✅ Con prefijo |
| Pub/Sub Topic | `attachments-finalized` | ⚠️ Sin prefijo (evaluar cambiar) |
| Secret | `corpchat-config` | ✅ Con prefijo |

### 3. Colecciones Firestore con Prefijo

**CAMBIO CRÍTICO**: Todas las colecciones de Firestore ahora usan prefijo `corpchat_`:

```python
# ❌ ANTES (peligroso en Firestore compartido)
collection('users')
collection('chats')
collection('attachments')

# ✅ AHORA (seguro en Firestore compartido)
collection('corpchat_users')
collection('corpchat_chats')
collection('corpchat_attachments')
```

**Implementado en**: `services/agents/shared/firestore_client.py`

```python
class FirestoreClient:
    COLLECTION_PREFIX = "corpchat_"
    
    def get_user(self, user_id: str):
        # Usa: corpchat_users
        self._db.collection(f'{self.COLLECTION_PREFIX}users')...
```

### 4. Labels Obligatorios

Todos los recursos tienen labels para identificación:

```yaml
labels:
  team: corpchat
  env: dev|stage|prod
  service: ui|gateway|orchestrator|etc
```

---

## 📋 Procedimiento Obligatorio ANTES de Deployment

### Paso 1: Auditoría

```bash
cd /Users/lufermalgo/Proyectos/CorpChat/infra/scripts
./audit_gcp.sh > audit_report_$(date +%Y%m%d).txt
```

**Revisar el reporte generado** y buscar:
- ⚠️ "YA EXISTE" - Recursos que colisionan
- ⚠️ Firestore database existente
- ⚠️ Colecciones Firestore existentes
- ⚠️ Services Cloud Run con nombre similar

### Paso 2: Decisión de Aislamiento

#### Opción A: Usar Proyecto Compartido (con precauciones)

**SI el reporte muestra:**
- ✅ Firestore NO existe o podemos usar colecciones con prefijo
- ✅ No hay Cloud Run services con prefijo "corpchat"
- ✅ No hay buckets con el nombre esperado

**ENTONCES**: 
- Proceder con prefijos en todos los recursos
- Usar colecciones Firestore con prefijo `corpchat_`
- Monitorear constantemente

#### Opción B: Proyecto GCP Separado (RECOMENDADO para dev)

**Crear proyecto nuevo para CorpChat:**

```bash
# Crear proyecto separado
gcloud projects create corpchat-dev-$(date +%s) \
  --name="CorpChat Development"

# Configurar billing
gcloud billing projects link corpchat-dev-XXXXX \
  --billing-account=YOUR_BILLING_ID

# Usar este proyecto para desarrollo
export PROJECT_ID=corpchat-dev-XXXXX
```

**PROS:**
- ✅ Aislamiento total
- ✅ Sin riesgo de afectar otros proyectos
- ✅ Costos separados y fáciles de monitorear
- ✅ Firestore dedicado

**CONTRAS:**
- ⏱️ Setup adicional
- 💰 Costo separado (pero con costo base = 0)

### Paso 3: Coordinación con Equipo

**ANTES de deployment:**

1. **Comunicar al equipo** que vas a deployar en `genai-385616`
2. **Verificar horarios** - No deployar durante ventanas críticas de otros proyectos
3. **Backup strategy** - Tener plan de rollback

---

## 🛡️ Protecciones Adicionales

### 1. Dry-Run Mode en Scripts

Todos los scripts deben soportar `--dry-run`:

```bash
./setup_gcp.sh --dry-run  # Muestra qué haría sin ejecutar
```

### 2. Confirmation Prompts

Scripts críticos deben pedir confirmación:

```bash
echo "⚠️  ¿Continuar con la creación de recursos? (yes/no)"
read -r confirmation
if [[ "$confirmation" != "yes" ]]; then
    exit 0
fi
```

### 3. Backup Antes de Modificar

Si Firestore existe, hacer backup:

```bash
gcloud firestore export gs://backup-bucket/firestore-backup-$(date +%Y%m%d)
```

---

## 🔍 Monitoreo Post-Deployment

### Verificar No-Colisión

Después de deployment, verificar:

```bash
# Listar SOLO recursos de CorpChat
gcloud run services list \
  --region=us-central1 \
  --filter="metadata.labels.team=corpchat"

# Verificar colecciones Firestore
gcloud firestore databases collections list \
  --database="(default)" \
  | grep "corpchat_"
```

### Alertas

Configurar alertas para:
- Modificaciones en recursos sin label `team=corpchat`
- Accesos a colecciones sin prefijo `corpchat_`
- Errores 403/404 que indiquen colisiones

---

## 📞 Contactos de Emergencia

**Si algo sale mal:**

1. **DETENER inmediatamente** cualquier deployment en progreso
2. **Verificar** que no se afectaron recursos de otros proyectos
3. **Notificar** al equipo
4. **Rollback** usando:
   ```bash
   gcloud run services update SERVICE \
     --region=us-central1 \
     --to-revisions=PREVIOUS_REVISION=100
   ```

---

## ✅ Checklist Pre-Deployment

Antes de ejecutar **CUALQUIER** comando que modifique GCP:

- [ ] Ejecuté `audit_gcp.sh` y revisé el reporte completo
- [ ] Verifiqué que NO existen colisiones de nombres
- [ ] Coordiné con el equipo sobre el deployment
- [ ] Tengo backup de Firestore (si existe)
- [ ] Entiendo qué hace cada comando antes de ejecutarlo
- [ ] Tengo plan de rollback documentado
- [ ] Configuré prefijos en TODOS los recursos
- [ ] Probé en proyecto de desarrollo separado (opcional pero recomendado)

---

## 🎯 Recomendación Final

### Para Desarrollo/Testing

**CREAR PROYECTO SEPARADO:**
```bash
# Opción más segura
export PROJECT_ID=corpchat-dev-$(whoami)-$(date +%s)
gcloud projects create $PROJECT_ID
# ... continuar setup
```

### Para Producción

**Usar proyecto compartido SOLO si:**
1. Auditoría confirma que es seguro
2. Equipo está coordinado
3. Todos los prefijos están en lugar
4. Hay monitoring activo

---

**Última actualización**: $(date)  
**Autor**: Implementación CorpChat MVP  
**Status**: 🚨 CRÍTICO - LEER ANTES DE DEPLOYMENT

