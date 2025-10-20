# Configuración de Conexión al Gateway - CorpChat

## 📋 Información de Conexión

### **URL del Gateway:**
```
https://corpchat-gateway-2s63drefva-uc.a.run.app
```

### **Clave de Autorización:**
```
corpchat-gateway
```

### **Tipo de Proveedor:**
```
OpenAI (compatible)
```

## 🔧 Configuración en Open WebUI

### **Pasos para Configurar:**

1. **Acceder a la interfaz de administración:**
   - URL: `https://corpchat-ui-2s63drefva-uc.a.run.app/admin/settings/connections`

2. **Configurar API OpenAI:**
   - **URL**: `https://corpchat-gateway-2s63drefva-uc.a.run.app`
   - **Autorización**: Bearer Token `corpchat-gateway`
   - **Tipo de Proveedor**: OpenAI
   - **IDs Modelo**: Dejar vacío (para incluir todos los modelos)

3. **Desactivar servicios no utilizados:**
   - **API Ollama**: Desactivado
   - **Conexiones Directas**: Desactivado
   - **Cachear Lista de Modelos**: Desactivado

## 🚨 Errores Comunes

### **Error de URL Truncada:**
- **❌ Incorrecta**: `corpchat-gateway-2s63drefva-uc.a.run.ap`
- **✅ Correcta**: `corpchat-gateway-2s63drefva-uc.a.run.app`

### **Síntomas del Error:**
```
ERROR | Connection error: Cannot connect to host corpchat-gateway-2s63drefva-uc.a.run.ap:443 ssl:default [Name or service not known]
```

## 📝 Variables de Entorno

### **En `services/ui/env-vars.yaml`:**
```yaml
# Configuración de API OpenAI (Gateway) - URL CORREGIDA Y DOCUMENTADA
# URL CORRECTA: https://corpchat-gateway-2s63drefva-uc.a.run.app
# CLAVE DE AUTORIZACIÓN: corpchat-gateway
OPENAI_API_BASE_URL: "https://corpchat-gateway-2s63drefva-uc.a.run.app"
OPENAI_API_KEY: "corpchat-gateway"
```

## ✅ Verificación

### **Test de Conectividad:**
```bash
curl -s "https://corpchat-gateway-2s63drefva-uc.a.run.app/models"
```

### **Respuesta Esperada:**
```json
{
  "object": "list",
  "data": [
    {"id": "gemini-auto", "object": "model", "created": 1677610602, "owned_by": "google"},
    {"id": "gemini-thinking", "object": "model", "created": 1677610602, "owned_by": "google"},
    {"id": "gemini-coding", "object": "model", "created": 1677610602, "owned_by": "google"},
    {"id": "gemini-analysis", "object": "model", "created": 1677610602, "owned_by": "google"},
    {"id": "gemini-fast", "object": "model", "created": 1677610602, "owned_by": "google"},
    {"id": "gemini-vision", "object": "model", "created": 1677610602, "owned_by": "google"}
  ]
}
```

## 🔄 Modelos Disponibles

| Modelo | Descripción | Capacidad |
|--------|-------------|-----------|
| `gemini-auto` | Selección automática según intención | General |
| `gemini-thinking` | Razonamiento profundo | Thinking |
| `gemini-coding` | Desarrollo y programación | Coding |
| `gemini-analysis` | Análisis de datos y documentos | Analysis |
| `gemini-fast` | Respuestas rápidas | Fast |
| `gemini-vision` | Análisis de imágenes | Vision |

## 📅 Última Actualización

**Fecha**: 2025-10-16  
**Versión**: 1.0  
**Estado**: ✅ Documentado y Verificado
