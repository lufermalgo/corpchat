# Open WebUI - Referencia Completa de Variables de Permisos

Este documento proporciona una referencia completa de todas las variables de entorno relacionadas con permisos en Open WebUI, organizadas por categorías y basada en los patrones reales de nomenclatura del código fuente.

## 🔍 Patrones de Nomenclatura

Open WebUI utiliza patrones consistentes para las variables de permisos:

- **Workspace Permissions**: `USER_PERMISSIONS_WORKSPACE_*`
- **Sharing Permissions**: `USER_PERMISSIONS_WORKSPACE_*_ALLOW_PUBLIC_SHARING` y `USER_PERMISSIONS_NOTES_ALLOW_PUBLIC_SHARING`
- **Chat Permissions**: `USER_PERMISSIONS_CHAT_*`
- **Features Permissions**: `USER_PERMISSIONS_FEATURES_*`

## 📋 Tabla de Contenidos

1. [Workspace Permissions](#workspace-permissions)
2. [Sharing Permissions](#sharing-permissions)
3. [Chat Permissions](#chat-permissions)
4. [Features Permissions](#features-permissions)
5. [Authentication & Access Control](#authentication--access-control)
6. [Audio & Media Permissions](#audio--media-permissions)
7. [Admin Permissions](#admin-permissions)
8. [Integration Permissions](#integration-permissions)
9. [Ejemplos de Configuración](#ejemplos-de-configuración)

---

## 🏢 Workspace Permissions

Controlan el acceso a diferentes áreas del workspace. **Patrón**: `USER_PERMISSIONS_WORKSPACE_*`

### Variables de Acceso al Workspace

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_WORKSPACE_MODELS_ACCESS` | Acceso a modelos en el workspace | `false` | Boolean |
| `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ACCESS` | Acceso a knowledge base en el workspace | `false` | Boolean |
| `USER_PERMISSIONS_WORKSPACE_PROMPTS_ACCESS` | Acceso a prompts en el workspace | `false` | Boolean |
| `USER_PERMISSIONS_WORKSPACE_TOOLS_ACCESS` | Acceso a herramientas en el workspace | `false` | Boolean |

### Variables de Control de Acceso Global

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `BYPASS_MODEL_ACCESS_CONTROL` | Omite el control de acceso a modelos | `false` | Boolean |
| `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS` | Admin puede acceder a contenido del workspace | `true` | Boolean |

---

## 🔗 Sharing Permissions

Controlan las capacidades de compartir contenido. **Nota**: Las variables de sharing siguen el patrón `USER_PERMISSIONS_WORKSPACE_*_ALLOW_PUBLIC_SHARING` y `USER_PERMISSIONS_NOTES_ALLOW_PUBLIC_SHARING`.

### Variables de Compartir Públicamente (Patrón: WORKSPACE_*_ALLOW_PUBLIC_SHARING)

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_WORKSPACE_MODELS_ALLOW_PUBLIC_SHARING` | Permitir compartir modelos públicamente | `false` | Boolean |
| `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_PUBLIC_SHARING` | Permitir compartir knowledge públicamente | `false` | Boolean |
| `USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_PUBLIC_SHARING` | Permitir compartir prompts públicamente | `false` | Boolean |
| `USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_PUBLIC_SHARING` | Permitir compartir herramientas públicamente | `false` | Boolean |
| `USER_PERMISSIONS_NOTES_ALLOW_PUBLIC_SHARING` | Permitir compartir notas públicamente | `false` | Boolean |

### Variables de Compartir en Chat (Patrón: CHAT_*)

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_CHAT_SHARE` | Permitir compartir conversaciones | `true` | Boolean |
| `ENABLE_COMMUNITY_SHARING` | Habilitar compartir en comunidad | `true` | Boolean |

---

## 💬 Chat Permissions

Controlan las funcionalidades del chat y la interfaz de conversación. **Patrón**: `USER_PERMISSIONS_CHAT_*`

### Variables de Controles del Chat

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_CHAT_CONTROLS` | Permitir controles del chat | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_VALVES` | Permitir válvulas del chat | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_SYSTEM_PROMPT` | Permitir modificar system prompt | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_PARAMS` | Permitir modificar parámetros | `true` | Boolean |

### Variables de Gestión de Conversaciones

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_CHAT_FILE_UPLOAD` | Permitir subir archivos | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_DELETE` | Permitir eliminar conversaciones | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_DELETE_MESSAGE` | Permitir eliminar mensajes | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_CONTINUE_RESPONSE` | Permitir continuar respuestas | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_REGENERATE_RESPONSE` | Permitir regenerar respuestas | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_RATE_RESPONSE` | Permitir calificar respuestas | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_EDIT` | Permitir editar conversaciones | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_EXPORT` | Permitir exportar conversaciones | `true` | Boolean |

### Variables de Chat Temporal

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_CHAT_TEMPORARY` | Permitir chat temporal | `true` | Boolean |
| `USER_PERMISSIONS_CHAT_TEMPORARY_ENFORCED` | Forzar chat temporal | `false` | Boolean |

### Variables de Modelos Múltiples

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_CHAT_MULTIPLE_MODELS` | Permitir múltiples modelos | `true` | Boolean |

---

## 🎯 Features Permissions

Controlan las características y funcionalidades avanzadas. **Patrón**: `USER_PERMISSIONS_FEATURES_*`

### Variables de Características Principales

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_FEATURES_DIRECT_TOOL_SERVERS` | Acceso directo a servidores de herramientas | `false` | Boolean |
| `USER_PERMISSIONS_FEATURES_WEB_SEARCH` | Permitir búsqueda web | `true` | Boolean |
| `USER_PERMISSIONS_FEATURES_IMAGE_GENERATION` | Permitir generación de imágenes | `true` | Boolean |
| `USER_PERMISSIONS_FEATURES_CODE_INTERPRETER` | Permitir intérprete de código | `true` | Boolean |
| `USER_PERMISSIONS_FEATURES_NOTES` | Permitir notas | `true` | Boolean |

### Variables de Características del Sistema

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `ENABLE_WEB_SEARCH` | Habilitar búsqueda web | `false` | Boolean |
| `ENABLE_IMAGE_GENERATION` | Habilitar generación de imágenes | `false` | Boolean |
| `ENABLE_CODE_INTERPRETER` | Habilitar intérprete de código | `true` | Boolean |
| `ENABLE_NOTES` | Habilitar notas | `true` | Boolean |
| `ENABLE_CODE_EXECUTION` | Habilitar ejecución de código | `true` | Boolean |
| `ENABLE_CHANNELS` | Habilitar canales | `false` | Boolean |

---

## 🔐 Authentication & Access Control

### Variables de Autenticación

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `ENABLE_SIGNUP` | Permitir registro de usuarios | `true` | Boolean |
| `ENABLE_LOGIN_FORM` | Habilitar formulario de login | `true` | Boolean |
| `ENABLE_API_KEY` | Habilitar claves API | `true` | Boolean |
| `ENABLE_API_KEY_ENDPOINT_RESTRICTIONS` | Restricciones en endpoints API | `false` | Boolean |

### Variables de OAuth

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `ENABLE_OAUTH_SIGNUP` | Permitir registro via OAuth | `false` | Boolean |
| `ENABLE_OAUTH_ROLE_MANAGEMENT` | Gestión de roles via OAuth | `false` | Boolean |
| `ENABLE_OAUTH_GROUP_MANAGEMENT` | Gestión de grupos via OAuth | `false` | Boolean |
| `ENABLE_OAUTH_GROUP_CREATION` | Creación de grupos via OAuth | `false` | Boolean |

### Variables de LDAP

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `ENABLE_LDAP` | Habilitar autenticación LDAP | `false` | Boolean |
| `ENABLE_LDAP_GROUP_MANAGEMENT` | Gestión de grupos LDAP | `false` | Boolean |
| `ENABLE_LDAP_GROUP_CREATION` | Creación de grupos LDAP | `false` | Boolean |

---

## 🎵 Audio & Media Permissions

### Variables de Speech-to-Text (STT)

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_CHAT_STT` | Permitir Speech-to-Text | `true` | Boolean |
| `AUDIO_STT_ENGINE` | Motor de STT (openai, azure, etc.) | `""` | String |

### Variables de Text-to-Speech (TTS)

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_CHAT_TTS` | Permitir Text-to-Speech | `true` | Boolean |
| `AUDIO_TTS_ENGINE` | Motor de TTS (openai, elevenlabs, azure, etc.) | `""` | String |

### Variables de Llamadas de Voz

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `USER_PERMISSIONS_CHAT_CALL` | Permitir llamadas de voz | `true` | Boolean |

---

## 👑 Admin Permissions

### Variables de Acceso Admin

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `ENABLE_ADMIN_EXPORT` | Admin puede exportar datos | `true` | Boolean |
| `ENABLE_ADMIN_CHAT_ACCESS` | Admin puede acceder a chats | `true` | Boolean |

---

## 🔌 Integration Permissions

### Variables de Integración de Almacenamiento

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `ENABLE_GOOGLE_DRIVE_INTEGRATION` | Integración con Google Drive | `false` | Boolean |
| `ENABLE_ONEDRIVE_INTEGRATION` | Integración con OneDrive | `false` | Boolean |
| `ENABLE_ONEDRIVE_PERSONAL` | OneDrive personal | `true` | Boolean |
| `ENABLE_ONEDRIVE_BUSINESS` | OneDrive business | `true` | Boolean |

### Variables de APIs Externas

| Variable | Descripción | Valor por Defecto | Tipo |
|----------|-------------|-------------------|------|
| `ENABLE_OPENAI_API` | Habilitar API de OpenAI | `true` | Boolean |
| `ENABLE_OLLAMA_API` | Habilitar API de Ollama | `true` | Boolean |
| `ENABLE_DIRECT_CONNECTIONS` | Conexiones directas | `false` | Boolean |

---

## 📝 Ejemplos de Configuración

### Configuración Restrictiva (CorpChat)

```yaml
# Workspace Permissions - Acceso limitado
USER_PERMISSIONS_WORKSPACE_MODELS_ACCESS: "false"
USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ACCESS: "false"
USER_PERMISSIONS_WORKSPACE_PROMPTS_ACCESS: "false"
USER_PERMISSIONS_WORKSPACE_TOOLS_ACCESS: "false"
BYPASS_MODEL_ACCESS_CONTROL: "false"

# Sharing Permissions - Sin compartir público
USER_PERMISSIONS_WORKSPACE_MODELS_ALLOW_PUBLIC_SHARING: "false"
USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_PUBLIC_SHARING: "false"
USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_PUBLIC_SHARING: "false"
USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_PUBLIC_SHARING: "false"
USER_PERMISSIONS_NOTES_ALLOW_PUBLIC_SHARING: "false"
USER_PERMISSIONS_CHAT_SHARE: "false"
ENABLE_COMMUNITY_SHARING: "false"

# Chat Permissions - Controles básicos
USER_PERMISSIONS_CHAT_CONTROLS: "false"
USER_PERMISSIONS_CHAT_TEMPORARY: "false"
USER_PERMISSIONS_CHAT_TEMPORARY_ENFORCED: "false"
USER_PERMISSIONS_CHAT_CALL: "false"

# Features Permissions - Solo características esenciales
USER_PERMISSIONS_FEATURES_WEB_SEARCH: "true"
USER_PERMISSIONS_FEATURES_IMAGE_GENERATION: "true"
USER_PERMISSIONS_FEATURES_CODE_INTERPRETER: "true"
USER_PERMISSIONS_FEATURES_NOTES: "false"  # ← Variable de permisos de usuario
ENABLE_WEB_SEARCH: "true"
ENABLE_IMAGE_GENERATION: "true"
ENABLE_CODE_INTERPRETER: "true"


# Audio & Media - Deshabilitado
USER_PERMISSIONS_CHAT_STT: "false"
USER_PERMISSIONS_CHAT_TTS: "false"
AUDIO_STT_ENGINE: ""
AUDIO_TTS_ENGINE: ""
```

### Configuración Permisiva (Desarrollo/Testing)

```yaml
# Workspace Permissions - Acceso completo
USER_PERMISSIONS_WORKSPACE_MODELS_ACCESS: "true"
USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ACCESS: "true"
USER_PERMISSIONS_WORKSPACE_PROMPTS_ACCESS: "true"
USER_PERMISSIONS_WORKSPACE_TOOLS_ACCESS: "true"
BYPASS_MODEL_ACCESS_CONTROL: "true"

# Sharing Permissions - Compartir habilitado
USER_PERMISSIONS_WORKSPACE_MODELS_ALLOW_PUBLIC_SHARING: "true"
USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_PUBLIC_SHARING: "true"
USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_PUBLIC_SHARING: "true"
USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_PUBLIC_SHARING: "true"
USER_PERMISSIONS_NOTES_ALLOW_PUBLIC_SHARING: "true"
USER_PERMISSIONS_CHAT_SHARE: "true"
ENABLE_COMMUNITY_SHARING: "true"

# Chat Permissions - Todos los controles
USER_PERMISSIONS_CHAT_CONTROLS: "true"
USER_PERMISSIONS_CHAT_TEMPORARY: "true"
USER_PERMISSIONS_CHAT_TEMPORARY_ENFORCED: "false"
USER_PERMISSIONS_CHAT_CALL: "true"

# Features Permissions - Todas las características
USER_PERMISSIONS_FEATURES_WEB_SEARCH: "true"
USER_PERMISSIONS_FEATURES_IMAGE_GENERATION: "true"
USER_PERMISSIONS_FEATURES_CODE_INTERPRETER: "true"
USER_PERMISSIONS_FEATURES_NOTES: "true"  # ← Variable de permisos de usuario
ENABLE_WEB_SEARCH: "true"
ENABLE_IMAGE_GENERATION: "true"
ENABLE_CODE_INTERPRETER: "true"
ENABLE_NOTES: "true"  # ← Variable de sistema

# Audio & Media - Habilitado
USER_PERMISSIONS_CHAT_STT: "true"
USER_PERMISSIONS_CHAT_TTS: "true"
AUDIO_STT_ENGINE: "openai"
AUDIO_TTS_ENGINE: "openai"
```

---

## 🔧 Notas Importantes

### Patrones de Nomenclatura Confirmados

Basado en el análisis del código fuente de Open WebUI v0.6.34:

1. **Workspace Permissions**: `USER_PERMISSIONS_WORKSPACE_*`
   - Acceso: `USER_PERMISSIONS_WORKSPACE_MODELS_ACCESS`
   - Sharing: `USER_PERMISSIONS_WORKSPACE_*_ALLOW_PUBLIC_SHARING`

2. **Sharing Permissions**: 
   - Workspace: `USER_PERMISSIONS_WORKSPACE_*_ALLOW_PUBLIC_SHARING`
   - Notes: `USER_PERMISSIONS_NOTES_ALLOW_PUBLIC_SHARING`
   - Chat: `USER_PERMISSIONS_CHAT_SHARE`

3. **Chat Permissions**: `USER_PERMISSIONS_CHAT_*`
   - Controles: `USER_PERMISSIONS_CHAT_CONTROLS`
   - Funcionalidades: `USER_PERMISSIONS_CHAT_FILE_UPLOAD`, `USER_PERMISSIONS_CHAT_DELETE`, etc.

4. **Features Permissions**: `USER_PERMISSIONS_FEATURES_*`
   - Características: `USER_PERMISSIONS_FEATURES_WEB_SEARCH`, `USER_PERMISSIONS_FEATURES_NOTES`, etc.

### Configuración Persistente

- **`ENABLE_PERSISTENT_CONFIG`**: Controla si las configuraciones se guardan en la base de datos
- **Valor recomendado**: `false` para desarrollo, `true` para producción
- **Efecto**: Si está en `false`, las variables de entorno siempre se aplican

### Precedencia de Variables

1. **Variables de entorno** (mayor precedencia)
2. **Configuraciones persistentes** (si `ENABLE_PERSISTENT_CONFIG=true`)
3. **Valores por defecto** (menor precedencia)

### Variables Duplicadas

Algunas funcionalidades tienen variables duplicadas:
- `USER_PERMISSIONS_FEATURES_*` vs `ENABLE_*`
- Usar ambas para máxima compatibilidad

---

## 📚 Referencias

- [Open WebUI Documentation](https://docs.open-webui.com/)
- [Open WebUI GitHub Repository](https://github.com/open-webui/open-webui)
- [Open WebUI Configuration Guide](https://docs.open-webui.com/getting-started/env-configuration/)

---

*Última actualización: Octubre 2025*
*Versión de Open WebUI: v0.6.34*
