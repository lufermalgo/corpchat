# Open WebUI - Análisis Técnico Profundo

**Fecha**: 15 de Octubre, 2025  
**Versión**: 1.0  
**Propósito**: Análisis técnico detallado de Open WebUI para integración óptima con CorpChat

---

## Resumen Ejecutivo

Open WebUI es una plataforma de interfaz de usuario avanzada para modelos de lenguaje, que proporciona capacidades robustas de streaming, procesamiento de documentos, transcripción de audio y gestión de sesiones. Este análisis técnico profundiza en las características clave para la integración con CorpChat.

---

## 1. Streaming (Server-Sent Events)

### 1.1 Implementación Técnica

Open WebUI implementa streaming usando **Server-Sent Events (SSE)** compatible con la API de OpenAI:

#### Formato de Streaming:
```json
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1699123456,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"Hola"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1699123456,"model":"gpt-4","choices":[{"index":0,"delta":{"content":" mundo"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1699123456,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

#### Headers Requeridos:
```http
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no  # Para compatibilidad con Nginx
```

### 1.2 Integración con CorpChat Gateway

**Problema Actual**: El Gateway retorna respuestas completas, no streaming incremental.

**Solución Requerida**:
1. Implementar generador asíncrono en `services/gateway/app.py`
2. Usar `StreamingResponse` de FastAPI
3. Configurar headers SSE apropiados
4. Manejar errores en streaming

### 1.3 Configuración Open WebUI

**Variables de entorno**:
```yaml
ENABLE_STREAMING: "true"  # Habilitar streaming
ENABLE_MESSAGE_RATING: "false"  # Deshabilitar rating para mejor UX
```

---

## 2. Speech-to-Text (STT)

### 2.1 Arquitectura STT

Open WebUI soporta múltiples providers de STT:

#### Providers Soportados:
- **OpenAI Whisper** (local y API)
- **DeepGram** (cloud)
- **WebAPI** (browser native)
- **Local Whisper** (on-premise)

### 2.2 Configuración Técnica

#### Variables de Entorno:
```yaml
# Configuración STT
AUDIO_STT_ENGINE: "openai"  # o "whisper", "deepgram"
AUDIO_STT_MODEL: "whisper-1"
AUDIO_STT_OPENAI_API_BASE_URL: "https://api.openai.com/v1"
AUDIO_STT_OPENAI_API_KEY: "sk-..."
AUDIO_STT_WHISPER_MODEL: "base"  # Para Whisper local
AUDIO_STT_LANGUAGE: "es"  # Código ISO 639-1
```

#### Endpoint de Transcripción:
```http
POST /api/audio/transcriptions
Content-Type: multipart/form-data

file: [audio_file]
model: whisper-1
language: es
```

### 2.3 Integración con CorpChat

**Estrategia Recomendada**:
1. Configurar Open WebUI para usar Gateway como provider STT
2. Gateway implementa endpoint `/v1/audio/transcriptions`
3. Gateway usa Google Cloud Speech-to-Text internamente
4. Retorna formato OpenAI-compatible

---

## 3. RAG (Retrieval Augmented Generation)

### 3.1 Pipeline de Documentos

Open WebUI implementa un pipeline robusto de procesamiento de documentos:

#### Flujo de Procesamiento:
1. **Upload**: `POST /api/v1/files/`
2. **Extracción**: Automática por tipo de archivo
3. **Chunking**: División semántica del contenido
4. **Embeddings**: Generación de vectores
5. **Storage**: Almacenamiento en base de datos vectorial

#### Formatos Soportados:
- **Documentos**: PDF, DOCX, TXT, MD
- **Hojas de cálculo**: XLSX, CSV
- **Presentaciones**: PPTX
- **Imágenes**: PNG, JPG (con OCR)
- **Audio**: MP3, WAV (con transcripción)
- **Video**: MP4 (extracción de audio + transcripción)

### 3.2 Configuración RAG

#### Variables de Entorno:
```yaml
# RAG Configuration
RAG_EMBEDDING_ENGINE: "ollama"  # o "openai"
RAG_EMBEDDING_MODEL: "nomic-embed-text"
RAG_CHUNK_SIZE: 512
RAG_CHUNK_OVERLAP: 128
RAG_TOP_K: 5
RAG_RELEVANCE_THRESHOLD: 0.7
```

#### Endpoints RAG:
```http
# Upload archivo
POST /api/v1/files/
Content-Type: multipart/form-data

# Crear knowledge collection
POST /api/v1/knowledge/
Content-Type: application/json

# Usar en chat
POST /api/chat/completions
Content-Type: application/json
{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "Pregunta"}],
  "files": [{"type": "file", "id": "file-id"}]
}
```

### 3.3 Integración con CorpChat

**Estado Actual**: CorpChat tiene pipeline completo implementado.

**Optimizaciones**:
1. Usar endpoint `/extract/process` existente
2. Validar formatos soportados
3. Mejorar manejo de errores
4. Implementar re-lectura de documentos

---

## 4. Gestión de Sesiones y Memoria

### 4.1 Organización de Conversaciones

Open WebUI implementa un sistema sofisticado de organización:

#### Características:
- **Folders**: Agrupación de conversaciones por proyecto
- **Tags**: Etiquetado flexible de conversaciones
- **System Prompts**: Prompts específicos por folder
- **Knowledge Attachments**: Archivos adjuntos automáticos

#### Estructura de Datos:
```json
{
  "folder_id": "folder-123",
  "folder_name": "Python Expert",
  "system_prompt": "Eres un experto en Python...",
  "attached_knowledge": ["knowledge-1", "knowledge-2"],
  "conversations": [
    {
      "chat_id": "chat-456",
      "title": "Debugging Python",
      "tags": ["python", "debugging"],
      "messages": [...]
    }
  ]
}
```

### 4.2 Memoria de Sesión

#### Working Memory:
- Últimos N mensajes de la conversación actual
- Contexto inmediato para respuestas coherentes
- Almacenado en memoria durante la sesión

#### Long-term Memory:
- Historial completo de conversaciones
- Búsqueda semántica en conversaciones pasadas
- Consolidación de contexto por proyecto

### 4.3 Integración con CorpChat

**Estrategia de Memoria Híbrida**:
1. **Working Memory**: Firestore (sesión actual)
2. **Long-term Memory**: BigQuery (embeddings históricos)
3. **User Profile**: Firestore (preferencias, contexto persistente)

---

## 5. API Endpoints Críticos

### 5.1 Chat Completions

```http
POST /api/chat/completions
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "gpt-4",
  "messages": [
    {"role": "user", "content": "Pregunta"}
  ],
  "stream": true,
  "files": [
    {"type": "file", "id": "file-id"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}
```

### 5.2 Model Management

```http
# Listar modelos disponibles
GET /api/models
Authorization: Bearer {token}

# Crear modelo personalizado
POST /api/models
Authorization: Bearer {token}
Content-Type: application/json
{
  "id": "custom-model",
  "name": "Modelo Personalizado",
  "api_base": "https://gateway-url/v1",
  "api_key": "sk-...",
  "capabilities": ["chat", "vision"]
}
```

### 5.3 File Management

```http
# Upload archivo
POST /api/v1/files/
Authorization: Bearer {token}
Content-Type: multipart/form-data

# Listar archivos
GET /api/v1/files/
Authorization: Bearer {token}

# Eliminar archivo
DELETE /api/v1/files/{file_id}
Authorization: Bearer {token}
```

---

## 6. Configuración de Producción

### 6.1 Variables de Entorno Críticas

```yaml
# Autenticación
OPENAI_API_KEY: "sk-..."
OPENAI_API_BASE: "https://gateway-url/v1"

# Streaming
ENABLE_STREAMING: "true"
STREAMING_BUFFER_SIZE: "8192"

# STT
AUDIO_STT_ENGINE: "openai"
AUDIO_STT_OPENAI_API_BASE_URL: "https://gateway-url/v1"

# RAG
RAG_EMBEDDING_ENGINE: "openai"
RAG_EMBEDDING_MODEL: "text-embedding-ada-002"

# UI
ENABLE_MESSAGE_RATING: "false"
ENABLE_FOLLOW_UP_GENERATION: "false"
ENABLE_COMMUNITY_SHARING: "false"
```

### 6.2 Headers de Seguridad

```http
# Headers requeridos para producción
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## 7. Integración con CorpChat Gateway

### 7.1 Mapeo de Endpoints

| Open WebUI Endpoint | CorpChat Gateway | Propósito |
|---------------------|------------------|-----------|
| `/api/chat/completions` | `/v1/chat/completions` | Chat con streaming |
| `/api/audio/transcriptions` | `/v1/audio/transcriptions` | STT con Google Cloud |
| `/api/v1/files/` | `/extract/process` | Upload y procesamiento |
| `/api/models` | `/v1/models` | Lista de modelos |

### 7.2 Headers de Usuario

Open WebUI envía headers de identificación:
```http
X-OpenWebUI-User-Email: user@company.com
X-OpenWebUI-User-Id: user-123
X-OpenWebUI-Session-Id: session-456
```

### 7.3 Autenticación

**Estrategia**:
1. Open WebUI maneja autenticación OAuth
2. Gateway valida tokens JWT
3. Headers de usuario para identificación
4. Service accounts para APIs GCP

---

## 8. Recomendaciones de Implementación

### 8.1 Streaming

1. **Implementar SSE** en Gateway con generador asíncrono
2. **Configurar headers** apropiados para Nginx
3. **Manejar errores** gracefully en streaming
4. **Optimizar latencia** primer token < 500ms

### 8.2 STT

1. **Usar Google Cloud STT** para mejor calidad
2. **Implementar endpoint** OpenAI-compatible
3. **Configurar gramática** avanzada
4. **Soporte multi-idioma** (es, en, pt)

### 8.3 RAG

1. **Aprovechar pipeline** existente de CorpChat
2. **Validar formatos** soportados
3. **Implementar re-lectura** de documentos
4. **Optimizar embeddings** con Vertex AI

### 8.4 Memoria

1. **Working Memory**: Firestore (sesión actual)
2. **Long-term Memory**: BigQuery (embeddings históricos)
3. **Consolidación**: Automática al finalizar sesión
4. **Retrieval**: Semántico con umbral de relevancia

---

## 9. Métricas y Monitoreo

### 9.1 KPIs de Streaming

- **Latencia primer token**: < 500ms
- **Throughput**: > 10 tokens/s
- **Tiempo total respuesta**: < 5s
- **Tasa de error**: < 1%

### 9.2 KPIs de STT

- **Precisión transcripción**: > 95%
- **Latencia transcripción**: < 2s
- **Soporte gramática**: 100%
- **Disponibilidad**: > 99.5%

### 9.3 KPIs de RAG

- **Éxito procesamiento**: 100% formatos soportados
- **Recall embeddings**: > 80%
- **Precisión retrieval**: > 70%
- **Tiempo procesamiento**: < 30s por documento

---

## 10. Conclusiones

Open WebUI proporciona una base sólida para la integración con CorpChat:

### Fortalezas:
- ✅ **API compatible** con OpenAI
- ✅ **Streaming robusto** con SSE
- ✅ **RAG avanzado** con múltiples formatos
- ✅ **STT configurable** con múltiples providers
- ✅ **Gestión de sesiones** sofisticada

### Oportunidades:
- 🔧 **Integración Gateway** para STT con Google Cloud
- 🔧 **Memoria híbrida** (Firestore + BigQuery)
- 🔧 **Pipeline optimizado** de documentos
- 🔧 **Streaming real-time** implementado

### Próximos Pasos:
1. Implementar streaming SSE en Gateway
2. Configurar STT con Google Cloud
3. Validar pipeline de documentos
4. Implementar memoria a largo plazo
5. Testing E2E completo

---

**Documento preparado por**: AI Assistant  
**Revisión técnica**: Pendiente  
**Aprobación**: Pendiente
