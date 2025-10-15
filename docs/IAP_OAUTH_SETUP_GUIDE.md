# Guía Completa: Configuración IAP OAuth 2.0 para CorpChat

**Tiempo estimado**: 10-15 minutos  
**Requisitos**: Acceso a GCP Console con permisos de Owner o Editor en `genai-385616`  
**Cuenta**: fmaldonado@summan.com

---

## 📋 **Preparación**

Antes de empezar, ten a mano esta información:

```yaml
Proyecto GCP: genai-385616
Dominio corporativo: summan.com
Email soporte: fmaldonado@summan.com
Nombre aplicación: CorpChat
Descripción: Plataforma conversacional corporativa con IA para Summan
```

---

## 🔐 **Paso 1: Configurar OAuth Consent Screen** (5-7 minutos)

### 1.1. Acceder a la consola

Abre en tu navegador:

```
https://console.cloud.google.com/apis/credentials/consent?project=genai-385616
```

O navega manualmente:
1. GCP Console → APIs & Services → OAuth consent screen
2. Asegúrate que el proyecto sea `genai-385616` (arriba a la izquierda)

### 1.2. Configurar el tipo de aplicación

**User Type**:
- ✅ Selecciona: **Internal** (solo usuarios de tu organización Google Workspace)
- ❌ NO selecciones "External" (permitiría usuarios externos)

**Razón**: CorpChat es solo para empleados de Summan con cuentas `@summan.com`

Click en **CREATE** o **CREAR**

### 1.3. Información de la aplicación

**App information**:

| Campo | Valor |
|-------|-------|
| App name | `CorpChat` |
| User support email | `fmaldonado@summan.com` |
| App logo | (Opcional) Upload logo corporativo si tienes |

**App domain** (Opcional por ahora):

Deja estos campos vacíos por el momento. Los completaremos después del primer deploy cuando tengamos las URLs de Cloud Run.

- Application home page: (vacío)
- Application privacy policy link: (vacío)
- Application terms of service link: (vacío)

**Developer contact information**:

| Campo | Valor |
|-------|-------|
| Email addresses | `fmaldonado@summan.com` |

Click en **SAVE AND CONTINUE** o **GUARDAR Y CONTINUAR**

### 1.4. Scopes (Alcances)

En la pantalla "Scopes":

- **NO agregues ningún scope adicional** para este MVP
- Los scopes por defecto (`email`, `profile`, `openid`) son suficientes
- Estos son automáticos para Internal apps

Click en **SAVE AND CONTINUE**

### 1.5. Resumen

Revisa la configuración:
- User Type: Internal
- App name: CorpChat
- Support email: fmaldonado@summan.com

Click en **BACK TO DASHBOARD** o **VOLVER AL PANEL**

✅ **OAuth Consent Screen configurado**

---

## 🔑 **Paso 2: Crear OAuth 2.0 Client ID** (3-5 minutos)

### 2.1. Acceder a Credentials

Abre en tu navegador:

```
https://console.cloud.google.com/apis/credentials?project=genai-385616
```

O navega:
1. GCP Console → APIs & Services → Credentials

### 2.2. Crear nuevo Client ID

1. Click en **+ CREATE CREDENTIALS** (arriba)
2. Selecciona **OAuth 2.0 Client ID**

### 2.3. Configurar el Client ID

**Application type**:
- Selecciona: **Web application**

**Name**:
```
CorpChat IAP Client
```

**Authorized JavaScript origins** (opcional):
- Deja vacío por ahora

**Authorized redirect URIs**:
- **IMPORTANTE**: Deja vacío por ahora
- Lo configuraremos después del deploy cuando tengamos la URL de Cloud Run
- El formato será: `https://CLOUD_RUN_URL/_gcp_gatekeeper/authenticate`

Click en **CREATE** o **CREAR**

### 2.4. Guardar credenciales

⚠️ **CRÍTICO**: Aparecerá un modal con tus credenciales:

```
Your Client ID
client-id-here.apps.googleusercontent.com

Your Client Secret  
secret-here
```

**COPIA ESTAS CREDENCIALES INMEDIATAMENTE**:

1. **Client ID**: Cópialo a un lugar seguro (notas, password manager)
2. **Client Secret**: Cópialo también

**Estas credenciales solo se muestran UNA VEZ**

Si las pierdes, tendrás que:
- Ir a Credentials
- Editar "CorpChat IAP Client"
- Regenerar el secret (click en "Reset secret")

✅ **OAuth Client ID creado**

---

## 💾 **Paso 3: Guardar credenciales en Secret Manager** (2-3 minutos)

### Opción A: Via consola web (Recomendado para MVP)

1. Abre:
   ```
   https://console.cloud.google.com/security/secret-manager?project=genai-385616
   ```

2. Click en **+ CREATE SECRET**

3. **Primera secret (Client ID)**:
   ```
   Name: iap-oauth-client-id
   Secret value: [pega tu Client ID aquí]
   Regions: Automatic
   ```
   Click **CREATE SECRET**

4. **Segunda secret (Client Secret)**:
   ```
   Name: iap-oauth-client-secret
   Secret value: [pega tu Client Secret aquí]
   Regions: Automatic
   ```
   Click **CREATE SECRET**

### Opción B: Via comando (Alternativa)

```bash
# Exportar como variables (temporal)
export IAP_CLIENT_ID="tu-client-id.apps.googleusercontent.com"
export IAP_CLIENT_SECRET="tu-client-secret"

# Crear secrets
echo -n "$IAP_CLIENT_ID" | gcloud secrets create iap-oauth-client-id \
  --data-file=- \
  --replication-policy="automatic" \
  --project=genai-385616

echo -n "$IAP_CLIENT_SECRET" | gcloud secrets create iap-oauth-client-secret \
  --data-file=- \
  --replication-policy="automatic" \
  --project=genai-385616

# Limpiar variables
unset IAP_CLIENT_ID
unset IAP_CLIENT_SECRET
```

✅ **Credenciales guardadas de forma segura**

---

## 📝 **Paso 4: Actualizar tu .env local** (1 minuto)

Abre `/Users/lufermalgo/Proyectos/CorpChat/.env` y agrega:

```bash
# IAP OAuth
IAP_CLIENT_ID=tu-client-id.apps.googleusercontent.com
IAP_CLIENT_SECRET=tu-client-secret

# Nota: Estos valores solo para desarrollo local
# En Cloud Run se cargan desde Secret Manager
```

**NO committees este archivo** (ya está en .gitignore)

---

## ✅ **Verificación**

Confirma que tienes:

- [x] OAuth Consent Screen configurado (Type: Internal)
- [x] OAuth Client ID creado (Type: Web application)
- [x] Client ID y Secret copiados
- [x] Secrets creados en Secret Manager:
  - `iap-oauth-client-id`
  - `iap-oauth-client-secret`
- [x] `.env` local actualizado

---

## 🚀 **Próximos Pasos (DESPUÉS del deploy)**

### 1. Obtener URL de Cloud Run

Después de deployar `corpchat-ui`:

```bash
gcloud run services describe corpchat-ui \
  --region=us-central1 \
  --format='value(status.url)'
```

Ejemplo de output:
```
https://corpchat-ui-abc123-uc.a.run.app
```

### 2. Actualizar Authorized Redirect URIs

1. Vuelve a: https://console.cloud.google.com/apis/credentials?project=genai-385616
2. Click en "CorpChat IAP Client"
3. En **Authorized redirect URIs**, agrega:
   ```
   https://corpchat-ui-abc123-uc.a.run.app/_gcp_gatekeeper/authenticate
   ```
4. Click **SAVE**

### 3. Habilitar IAP en Cloud Run

```bash
# Obtener el backend service name
gcloud compute backend-services list --global | grep corpchat

# Habilitar IAP
gcloud iap web enable \
  --resource-type=backend-services \
  --service=BACKEND_SERVICE_NAME \
  --oauth2-client-id=$IAP_CLIENT_ID \
  --oauth2-client-secret=$IAP_CLIENT_SECRET
```

### 4. Configurar acceso de usuarios

```bash
# Agregar usuarios individuales
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=BACKEND_SERVICE_NAME \
  --member=user:fmaldonado@summan.com \
  --role=roles/iap.httpsResourceAccessor

# O agregar grupo entero
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=BACKEND_SERVICE_NAME \
  --member=group:equipo-genai@summan.com \
  --role=roles/iap.httpsResourceAccessor
```

---

## 🐛 **Troubleshooting**

### Problema: "OAuth consent screen not configured"

**Solución**: Vuelve al Paso 1 y completa la configuración del OAuth consent screen.

### Problema: "Invalid redirect URI"

**Causas**:
1. No actualizaste el redirect URI después del deploy
2. La URL tiene un typo
3. Falta el path `/_gcp_gatekeeper/authenticate`

**Solución**: Verifica la URL exacta del servicio Cloud Run y actualiza el redirect URI.

### Problema: "Access denied" al intentar acceder

**Causas**:
1. Tu usuario no tiene el rol `roles/iap.httpsResourceAccessor`
2. IAP no está habilitado correctamente

**Solución**:
```bash
# Verificar IAP status
gcloud iap web get-iam-policy \
  --resource-type=backend-services \
  --service=BACKEND_SERVICE_NAME

# Agregar tu usuario
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=BACKEND_SERVICE_NAME \
  --member=user:fmaldonado@summan.com \
  --role=roles/iap.httpsResourceAccessor
```

### Problema: "Client secret was reset"

Si regeneraste el secret:
1. Actualiza el secret en Secret Manager
2. Redeploya los servicios Cloud Run que usan IAP
3. Espera 5-10 minutos para propagación

---

## 📚 **Referencias**

- [IAP Documentation](https://cloud.google.com/iap/docs)
- [OAuth 2.0 Setup](https://cloud.google.com/iap/docs/enabling-oauth)
- [Cloud Run with IAP](https://cloud.google.com/iap/docs/enabling-cloud-run)

---

## 📞 **Contacto**

Si tienes problemas con esta configuración:

1. Revisa los logs de Cloud Run:
   ```bash
   gcloud run services logs read corpchat-ui --region=us-central1 --limit=50
   ```

2. Verifica el status de IAP:
   ```bash
   gcloud iap web get-iam-policy \
     --resource-type=backend-services \
     --service=BACKEND_SERVICE_NAME
   ```

3. Consulta con el equipo de seguridad de Summan si hay políticas organizacionales que puedan estar bloqueando IAP

---

**Última actualización**: $(date)  
**Autor**: CorpChat MVP Team  
**Status**: ✅ GUÍA COMPLETA

