# Configuración de Sugerencias de Prompts en Open WebUI

## 📋 Resumen

Este documento explica cómo configurar las sugerencias de prompts en Open WebUI para que estén deshabilitadas por defecto.

## 🎯 Objetivo

Deshabilitar completamente las sugerencias de prompts iniciales que aparecen en la interfaz de usuario para mantener una experiencia limpia y profesional.

## 🔧 Configuración Actual

### Variables de Entorno Configuradas

```yaml
# En services/ui/Dockerfile y services/ui/env-vars.yaml
DEFAULT_PROMPT_SUGGESTIONS: "[]"
ENABLE_FOLLOW_UP_GENERATION: "false"
ENABLE_PERSISTENT_CONFIG: "false"
```

### Explicación de Variables

- **`DEFAULT_PROMPT_SUGGESTIONS: "[]"`**: Lista vacía de sugerencias por defecto
- **`ENABLE_FOLLOW_UP_GENERATION: "false"`**: Deshabilita preguntas de seguimiento automáticas
- **`ENABLE_PERSISTENT_CONFIG: "false"`**: Permite que las variables de entorno se apliquen sin ser sobrescritas por configuraciones persistentes

## 📚 Proceso de Configuración

### Método 1: Configuración Manual (Recomendado)

1. **Acceder a la interfaz de administración**:
   - Ir a `http://localhost:8082/admin` (local) o la URL de administración
   - Iniciar sesión como administrador

2. **Eliminar sugerencias existentes**:
   - Navegar a la sección de **Settings** → **Interface**
   - Buscar la sección **"Default Prompt Suggestions"**
   - Eliminar todas las sugerencias existentes
   - Guardar la configuración

3. **Verificar resultado**:
   - La sección "Sugerido" ya no debería aparecer en la interfaz de usuario
   - No deberían mostrarse sugerencias de prompts iniciales

### Método 2: Variables de Entorno (Actual)

Las variables de entorno están configuradas para mantener las sugerencias vacías por defecto:

```dockerfile
ENV DEFAULT_PROMPT_SUGGESTIONS="[]"
ENV ENABLE_FOLLOW_UP_GENERATION=false
ENV ENABLE_PERSISTENT_CONFIG=false
```

## ⚠️ Limitaciones de Open WebUI

### Problema Identificado

Open WebUI v0.6.34 tiene una **lógica hardcodeada** que repuebla automáticamente las sugerencias cuando la lista está vacía:

```python
# Código interno de Open WebUI
if not config.DEFAULT_PROMPT_SUGGESTIONS:
    config.DEFAULT_PROMPT_SUGGESTIONS = [
        {"title": ["Hello!"], "content": "Hello!"},
        {"title": ["How are you?"], "content": "How are you?"},
        {"title": ["What can you do?"], "content": "What can you do?"},
    ]
```

### Solución

La **configuración manual desde la interfaz de administración** es la forma más efectiva de eliminar completamente las sugerencias, ya que:

1. Sobrescribe la lógica hardcodeada
2. Se guarda en la base de datos como configuración persistente
3. No se ve afectada por las variables de entorno

## 🔄 Proceso de Reconstrucción

### Para Nuevas Instalaciones

1. **Configurar variables de entorno** (ya configuradas)
2. **Iniciar el servicio**:
   ```bash
   docker-compose up -d corpchat-ui
   ```
3. **Acceder como administrador** y eliminar sugerencias manualmente
4. **Guardar configuración** en la interfaz de administración

### Para Reconstrucciones

1. **Detener el servicio**:
   ```bash
   docker-compose stop corpchat-ui
   docker-compose rm -f corpchat-ui
   ```

2. **Eliminar volumen de datos** (si se desea configuración fresca):
   ```bash
   docker volume rm corpchat-ui-data
   ```

3. **Reconstruir e iniciar**:
   ```bash
   docker-compose build corpchat-ui
   docker-compose up -d corpchat-ui
   ```

4. **Reconfigurar sugerencias manualmente** si es necesario

## ✅ Estado Actual

- ✅ **CSS personalizado eliminado** (no era necesario)
- ✅ **Variables de entorno configuradas** correctamente
- ✅ **Sugerencias deshabilitadas** mediante configuración manual
- ✅ **Configuración documentada** para futuras implementaciones

## 📝 Notas Importantes

1. **La configuración manual es persistente** y se mantiene entre reconstrucciones del contenedor
2. **Las variables de entorno actúan como respaldo** para nuevas instalaciones
3. **No es necesario CSS personalizado** una vez configurado correctamente
4. **El proceso debe repetirse** solo si se elimina completamente el volumen de datos

---

*Última actualización: Octubre 2025*
*Open WebUI versión: v0.6.34*
