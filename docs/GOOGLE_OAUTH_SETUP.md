# Configuración de Google OAuth para CorpChat

**Última actualización**: 15 Octubre 2025

---

## 🎯 **Objetivo**

Configurar autenticación de Google OAuth para que los usuarios puedan acceder a CorpChat con sus cuentas corporativas de Google.

---

## 📋 **Pasos para Configurar Google OAuth**

### **PASO 1: Crear Credenciales OAuth en Google Cloud Console**

1. **Ir a Google Cloud Console**:
   - URL: https://console.cloud.google.com/
   - Proyecto: `genai-385616`

2. **Navegar a APIs & Services**:
   - Menú lateral → "APIs & Services" → "Credentials"

3. **Crear Credenciales OAuth 2.0**:
   - Clic en "Create Credentials" → "OAuth 2.0 Client IDs"
   - Application type: "Web application"
   - Name: "CorpChat Open WebUI"

4. **Configurar URIs de Redirección**:
   ```
   Authorized redirect URIs:
   https://corpchat-ui-2s63drefva-uc.a.run.app/auth/oauth/callback/google
   ```

5. **Obtener Credenciales**:
   - Client ID: `[TU_CLIENT_ID]`
   - Client Secret: `[TU_CLIENT_SECRET]`

### **PASO 2: Configurar Variables de Entorno**

Una vez obtenidas las credenciales, actualizar el Dockerfile:

```dockerfile
ENV OAUTH_GOOGLE_CLIENT_ID="TU_CLIENT_ID_AQUI"
ENV OAUTH_GOOGLE_CLIENT_SECRET="TU_CLIENT_SECRET_AQUI"
```

### **PASO 3: Re-deployar Open WebUI**

```bash
# Re-deployar con las nuevas variables
gcloud builds submit --config=services/ui/cloudbuild.yaml --project=genai-385616
```

---

## 🔧 **Configuración Actual**

### **Variables de Entorno Configuradas**:
```bash
ENV ENABLE_OAUTH_SIGNUP=true
ENV OAUTH_GOOGLE_CLIENT_ID=""  # ← PENDIENTE: Configurar
ENV OAUTH_GOOGLE_CLIENT_SECRET=""  # ← PENDIENTE: Configurar
ENV OAUTH_GOOGLE_SCOPE="openid email profile"
ENV OAUTH_GOOGLE_REDIRECT_URI="https://corpchat-ui-2s63drefva-uc.a.run.app/auth/oauth/callback/google"
ENV OAUTH_MERGE_ACCOUNTS_BY_EMAIL=true
```

### **URL de Redirección**:
```
https://corpchat-ui-2s63drefva-uc.a.run.app/auth/oauth/callback/google
```

---

## 🧪 **Testing**

Una vez configurado:

1. **Ir a**: https://corpchat-ui-2s63drefva-uc.a.run.app
2. **Verificar**: Botón "Sign in with Google" aparece
3. **Probar**: Login con cuenta corporativa de Google
4. **Verificar**: Acceso a CorpChat con modelos disponibles

---

## 🚨 **Notas Importantes**

1. **Dominio Verificado**: Asegurar que el dominio `corpchat-ui-2s63drefva-uc.a.run.app` esté verificado en Google Cloud Console
2. **Cuentas Corporativas**: Configurar para permitir solo cuentas del dominio corporativo
3. **Seguridad**: Mantener el Client Secret seguro y no exponerlo en logs

---

## 📞 **Siguiente Paso**

**¿Quieres que proceda con la configuración de Google OAuth?**

1. ✅ **SÍ**: Te guío paso a paso para crear las credenciales
2. ❌ **NO**: Continuamos con pruebas usando cuenta local por ahora
