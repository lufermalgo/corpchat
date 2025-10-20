# Corregir Error OAuth: redirect_uri_mismatch

**Error actual**: `Error 400: redirect_uri_mismatch`

---

## 🔧 **Solución: Actualizar URL de Redirección en Google Cloud Console**

### **PASO 1: Ir a Google Cloud Console**
1. Abre: https://console.cloud.google.com/
2. Selecciona el proyecto: **genai-385616**

### **PASO 2: Navegar a Credenciales OAuth**
1. En el menú lateral, ve a **"APIs & Services"**
2. Selecciona **"Credentials"**

### **PASO 3: Editar OAuth 2.0 Client ID**
1. Busca el OAuth 2.0 Client ID que creaste (probablemente se llama "CorpChat Open WebUI" o similar)
2. Haz clic en el **icono de editar** (lápiz) a la derecha

### **PASO 4: Corregir Authorized redirect URIs**
1. En la sección **"Authorized redirect URIs"**
2. **ELIMINA** la URL actual (si existe):
   ```
   https://corpchat-ui-2s63drefva-uc.a.run.app/auth/oauth/callback/google
   ```
3. **AGREGA** la URL correcta:
   ```
   https://corpchat-ui-2s63drefva-uc.a.run.app/oauth/google/callback
   ```

### **PASO 5: Guardar Cambios**
1. Haz clic en **"Save"**
2. Espera unos segundos para que los cambios se apliquen

---

## ✅ **URLs Correctas para CorpChat**

### **Authorized JavaScript origins:**
```
https://corpchat-ui-2s63drefva-uc.a.run.app
```

### **Authorized redirect URIs:**
```
https://corpchat-ui-2s63drefva-uc.a.run.app/oauth/google/callback
```

---

## 🧪 **Probar Después del Cambio**

1. **Espera 1-2 minutos** para que Google aplique los cambios
2. **Ve a**: https://corpchat-ui-2s63drefva-uc.a.run.app
3. **Haz clic en**: "Continue with Google"
4. **Debería funcionar** sin el error `redirect_uri_mismatch`

---

## 📋 **Verificación**

Si el error persiste, verifica que:
- ✅ El proyecto correcto está seleccionado (genai-385616)
- ✅ La URL de redirección es exactamente: `/oauth/google/callback`
- ✅ No hay espacios extra o caracteres especiales
- ✅ Has guardado los cambios en Google Cloud Console

---

## 🆘 **Si Aún No Funciona**

Si después de estos pasos el error persiste:
1. Verifica que el Client ID y Client Secret son correctos
2. Asegúrate de que el dominio esté verificado en Google Cloud Console
3. Revisa los logs del servicio para más detalles
