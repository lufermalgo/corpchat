# Análisis de Estrategias de Memoria - CorpChat

**Fecha**: 15 de Octubre, 2025  
**Versión**: 1.0  
**Propósito**: Análisis comparativo de estrategias de memoria para implementar memoria a largo plazo en CorpChat

---

## Resumen Ejecutivo

Este documento analiza las estrategias de memoria disponibles en ADK, Open WebUI y Firestore para diseñar una solución híbrida que combine memoria a corto plazo (working memory) con memoria a largo plazo (long-term memory) para CorpChat.

---

## 1. Análisis de ADK Memory Management

### 1.1 Session State en ADK

ADK implementa un sistema de **session state** que persiste automáticamente:

#### Características:
- **Context Object**: `tool_context.state['key'] = value`
- **Persistencia Automática**: Estado se guarda después de cada callback
- **Disponibilidad**: Estado disponible inmediatamente después de escribir
- **Lifecycle**: Persistido automáticamente en la sesión

#### Ejemplo de Uso:
```python
# En cualquier callback
def before_agent_callback(context):
    context.state['user_preference'] = 'technical'
    context.state['project_context'] = 'corpchat'

def after_model_callback(context):
    # El estado ya está disponible
    preference = context.state.get('user_preference')
```

#### Limitaciones:
- ❌ **Solo por sesión**: No persiste entre sesiones
- ❌ **Sin búsqueda semántica**: No permite retrieval por contenido
- ❌ **Memoria limitada**: Solo para contexto inmediato

### 1.2 ADK Live API Integration

ADK Live integra con **Gemini Live API** para:
- **Audio transcription**: Input/output transcription
- **Session Events**: Transcripciones agregadas como eventos
- **Artifacts**: Audio guardado con referencia en eventos

#### Implicaciones para Memoria:
- ✅ **Eventos estructurados**: Transcripciones como eventos
- ✅ **Referencias a artifacts**: Audio/video con metadata
- ⚠️ **Limitado a sesión**: No hay persistencia cross-session

---

## 2. Análisis de Open WebUI Session Management

### 2.1 Organización de Conversaciones

Open WebUI implementa un sistema sofisticado:

#### Estructura:
```
Folders/
├── Project A/
│   ├── Conversation 1
│   ├── Conversation 2
│   └── System Prompt + Knowledge
└── Project B/
    ├── Conversation 3
    └── Conversation 4
```

#### Características:
- **Folders**: Agrupación por proyecto con contexto específico
- **System Prompts**: Por folder para personalización
- **Knowledge Attachments**: Archivos automáticamente incluidos
- **Tags**: Etiquetado flexible para búsqueda

### 2.2 Memoria de Sesión

#### Working Memory:
- **Últimos N mensajes**: Contexto inmediato
- **Session state**: Variables de sesión
- **Active context**: Archivos/knowledge activos

#### Long-term Memory:
- **Historial completo**: Todas las conversaciones
- **Búsqueda semántica**: En conversaciones pasadas
- **Cross-session retrieval**: Recuperación entre sesiones

### 2.3 Limitaciones Identificadas:
- ❌ **No integra con BigQuery**: Solo base de datos local
- ❌ **Sin embeddings históricos**: No hay retrieval semántico avanzado
- ❌ **Escalabilidad limitada**: Para múltiples usuarios/empresas

---

## 3. Estado Actual de CorpChat

### 3.1 Implementación Actual

#### Firestore Structure:
```
corpchat_users/
├── {user_id}/
│   ├── sesiones/
│   │   └── {session_id}/
│   │       ├── turnos/
│   │       │   └── {turn_id}/
│   │       └── metadata
│   └── profile/
```

#### BigQuery Structure:
```
corpchat.embeddings/
├── chunk_id (STRING)
├── attachment_id (STRING)
├── chat_id (STRING)
├── user_id (STRING)
├── text (STRING)
├── embedding (ARRAY<FLOAT64>)
├── source_filename (STRING)
├── chunk_index (INT64)
├── extraction_method (STRING)
└── created_at (TIMESTAMP)
```

### 3.2 Problemas Identificados:
- ❌ **Sin memoria a largo plazo**: No hay retrieval de conversaciones pasadas
- ❌ **Sin consolidación**: Sesiones no se consolidan en memoria histórica
- ❌ **Context window limitado**: Solo contexto de sesión actual

---

## 4. Estrategia de Memoria Híbrida Recomendada

### 4.1 Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORIA HÍBRIDA CORPCHAT                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Working Memory  │    │ Long-term       │    │ User Profile    │
│ (Firestore)     │    │ Memory          │    │ (Firestore)     │
│                 │    │ (BigQuery)      │    │                 │
│ • Últimos 10    │    │ • Embeddings    │    │ • Preferencias  │
│   turnos        │    │   históricos    │    │ • Contexto      │
│ • Session state │    │ • Retrieval     │    │   persistente   │
│ • Active files  │    │   semántico     │    │ • Metadata      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Memory Service  │
                    │ (Gateway)       │
                    │                 │
                    │ • Consolidación │
                    │ • Retrieval     │
                    │ • Context       │
                    │   enrichment    │
                    └─────────────────┘
```

### 4.2 Componentes de la Solución

#### 1. Working Memory (Corto Plazo)
**Ubicación**: Firestore  
**Propósito**: Contexto inmediato para respuestas coherentes

```python
async def get_working_memory(user_id: str, session_id: str, max_turns: int = 10):
    """
    Recupera memoria a corto plazo (últimos N turnos).
    
    Returns:
        Lista de mensajes [{role, content}] de turnos recientes
    """
    session_ref = firestore_client.collection(
        f"corpchat_users/{user_id}/sesiones"
    ).document(session_id)
    
    turnos = (
        session_ref.collection("turnos")
        .order_by("turn_number", direction=firestore.Query.DESCENDING)
        .limit(max_turns)
        .stream()
    )
    
    messages = []
    for turno in turnos:
        data = turno.to_dict()
        messages.extend(data.get("messages", []))
    
    return list(reversed(messages))
```

#### 2. Long-term Memory (Largo Plazo)
**Ubicación**: BigQuery  
**Propósito**: Retrieval semántico de conversaciones históricas

```sql
-- Tabla para memoria a largo plazo
CREATE TABLE `genai-385616.corpchat.conversation_memory` (
  user_id STRING NOT NULL,
  session_id STRING NOT NULL,
  conversation_text STRING NOT NULL,
  embedding ARRAY<FLOAT64> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  turn_count INT64 NOT NULL,
  summary TEXT,
  tags ARRAY<STRING>
)
PARTITION BY DATE(created_at)
CLUSTER BY user_id, session_id;
```

```python
async def get_long_term_memory(
    user_id: str,
    current_query: str,
    max_results: int = 5,
    similarity_threshold: float = 0.7
):
    """
    Recupera conversaciones pasadas relevantes usando embeddings.
    """
    # Generar embedding del query actual
    query_embedding = embedding_model.get_embeddings([current_query])[0].values
    
    # Búsqueda semántica en BigQuery
    query = f"""
    WITH query_embedding AS (
        SELECT {query_embedding} as embedding
    ),
    similarities AS (
        SELECT
            user_id,
            session_id,
            conversation_text,
            created_at,
            turn_count,
            ML.DISTANCE(embedding, (SELECT embedding FROM query_embedding), 'COSINE') as distance
        FROM `genai-385616.corpchat.conversation_memory`
        WHERE user_id = @user_id
        AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    )
    SELECT *
    FROM similarities
    WHERE distance <= @distance_threshold
    ORDER BY distance ASC
    LIMIT @max_results
    """
    
    # Ejecutar query y retornar contextos relevantes
    return contexts
```

#### 3. User Profile (Perfil de Usuario)
**Ubicación**: Firestore  
**Propósito**: Contexto persistente y preferencias

```python
async def get_user_profile(user_id: str):
    """
    Recupera perfil de usuario con contexto persistente.
    """
    user_ref = firestore_client.collection("corpchat_users").document(user_id)
    profile = user_ref.get()
    
    return {
        "preferences": profile.get("preferences", {}),
        "context": profile.get("context", ""),
        "expertise_areas": profile.get("expertise_areas", []),
        "recent_projects": profile.get("recent_projects", [])
    }
```

#### 4. Consolidación de Memoria
**Proceso**: Automático al finalizar sesión

```python
async def consolidate_session_memory(user_id: str, session_id: str):
    """
    Consolida sesión completada en memoria a largo plazo.
    """
    # 1. Recuperar todos los turnos de la sesión
    turnos = get_session_turns(user_id, session_id)
    
    # 2. Concatenar conversación completa
    full_conversation = concatenate_conversation(turnos)
    
    # 3. Generar embedding de la conversación completa
    embedding = embedding_model.get_embeddings([full_conversation])[0].values
    
    # 4. Generar resumen usando Gemini
    summary = generate_conversation_summary(full_conversation)
    
    # 5. Extraer tags automáticamente
    tags = extract_conversation_tags(full_conversation)
    
    # 6. Almacenar en BigQuery
    insert_into_conversation_memory({
        "user_id": user_id,
        "session_id": session_id,
        "conversation_text": full_conversation,
        "embedding": embedding,
        "summary": summary,
        "tags": tags,
        "turn_count": len(turnos)
    })
    
    # 7. Actualizar perfil de usuario
    update_user_profile(user_id, {
        "last_session": session_id,
        "total_sessions": firestore.Increment(1),
        "last_activity": datetime.now().isoformat()
    })
```

---

## 5. Integración con ADK

### 5.1 Memory Service en Gateway

```python
class MemoryService:
    def __init__(self, project_id: str):
        self.firestore_client = firestore.Client(project=project_id)
        self.bq_client = bigquery.Client(project=project_id)
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    async def enrich_context(self, user_id: str, session_id: str, current_query: str):
        """
        Enriquece contexto con memoria a corto y largo plazo.
        """
        # 1. Working memory (corto plazo)
        working_memory = await self.get_working_memory(user_id, session_id)
        
        # 2. Long-term memory (largo plazo)
        long_term_context = await self.get_long_term_memory(user_id, current_query)
        
        # 3. User profile
        user_profile = await self.get_user_profile(user_id)
        
        # 4. Construir contexto enriquecido
        enhanced_context = self.build_enhanced_context(
            working_memory,
            long_term_context,
            user_profile,
            current_query
        )
        
        return enhanced_context
```

### 5.2 Integración en Chat Completions

```python
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, ...):
    # ... código existente ...
    
    # ENRIQUECER CONTEXTO CON MEMORIA
    memory_service = MemoryService(project_id=PROJECT_ID)
    
    enhanced_context = await memory_service.enrich_context(
        user_id=user_id,
        session_id=session_id,
        current_query=user_message
    )
    
    # Agregar contexto enriquecido a los mensajes
    messages_with_memory = [
        Content(role="user", parts=[Part.from_text(enhanced_context)])
    ]
    
    # ... continuar con generación de respuesta ...
    
    # GUARDAR TURNO Y CONSOLIDAR SI ES NECESARIO
    await save_conversation_to_firestore(...)
    
    # Consolidar sesión si es el último turno o sesión cerrada
    if is_session_complete:
        await memory_service.consolidate_session_memory(user_id, session_id)
```

---

## 6. Estrategias de Retrieval

### 6.1 Retrieval Semántico

#### Embeddings:
- **Modelo**: `text-embedding-004` (Vertex AI)
- **Dimensiones**: 768
- **Uso**: Búsqueda por similitud coseno

#### Query Optimization:
```sql
-- Query optimizado para retrieval
WITH query_embedding AS (
    SELECT @query_embedding as embedding
),
similarities AS (
    SELECT
        *,
        ML.DISTANCE(embedding, (SELECT embedding FROM query_embedding), 'COSINE') as distance
    FROM `genai-385616.corpchat.conversation_memory`
    WHERE user_id = @user_id
    AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
)
SELECT *
FROM similarities
WHERE distance <= @threshold
ORDER BY distance ASC
LIMIT @max_results
```

### 6.2 Context Window Optimization

#### Estrategia de Ventana Deslizante:
```python
def optimize_context_window(
    working_memory: list,
    long_term_context: list,
    max_tokens: int = 4000
):
    """
    Optimiza ventana de contexto para no exceder límites.
    """
    # 1. Priorizar working memory (más reciente)
    context_tokens = 0
    optimized_context = []
    
    # 2. Agregar working memory primero
    for message in working_memory:
        tokens = count_tokens(message["content"])
        if context_tokens + tokens <= max_tokens * 0.6:  # 60% para working memory
            optimized_context.append(message)
            context_tokens += tokens
    
    # 3. Agregar long-term memory si hay espacio
    remaining_tokens = max_tokens - context_tokens
    for context in long_term_context:
        tokens = count_tokens(context["text"])
        if context_tokens + tokens <= max_tokens:
            optimized_context.append({
                "role": "system",
                "content": f"[Contexto histórico: {context['text'][:200]}...]"
            })
            context_tokens += tokens
    
    return optimized_context
```

---

## 7. Configuración de BigQuery

### 7.1 Tabla de Memoria a Largo Plazo

```sql
-- Crear tabla para memoria a largo plazo
CREATE TABLE `genai-385616.corpchat.conversation_memory` (
  user_id STRING NOT NULL,
  session_id STRING NOT NULL,
  conversation_text STRING NOT NULL,
  embedding ARRAY<FLOAT64> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  turn_count INT64 NOT NULL,
  summary TEXT,
  tags ARRAY<STRING>,
  relevance_score FLOAT64
)
PARTITION BY DATE(created_at)
CLUSTER BY user_id, session_id;

-- Índice para búsquedas rápidas
CREATE INDEX idx_conversation_memory_user_date 
ON `genai-385616.corpchat.conversation_memory` (user_id, created_at);

-- Política de retención (opcional)
ALTER TABLE `genai-385616.corpchat.conversation_memory`
SET OPTIONS(
  description="Memoria a largo plazo de conversaciones con embeddings para retrieval semántico",
  partition_expiration_days=365  -- Retener por 1 año
);
```

### 7.2 Permisos IAM

```bash
# Permisos para service account
gcloud projects add-iam-policy-binding genai-385616 \
    --member=serviceAccount:corpchat-app@genai-385616.iam.gserviceaccount.com \
    --role=roles/bigquery.dataEditor

gcloud projects add-iam-policy-binding genai-385616 \
    --member=serviceAccount:corpchat-app@genai-385616.iam.gserviceaccount.com \
    --role=roles/bigquery.jobUser
```

---

## 8. Métricas y Monitoreo

### 8.1 KPIs de Memoria

#### Working Memory:
- **Latencia recuperación**: < 100ms
- **Turnos recuperados**: 10 (configurable)
- **Disponibilidad**: > 99.9%

#### Long-term Memory:
- **Recall**: > 80% en contextos relevantes
- **Precisión**: > 70% en retrieval semántico
- **Latencia búsqueda**: < 500ms
- **Consolidación**: 100% de sesiones completadas

#### User Profile:
- **Actualización**: Real-time
- **Persistencia**: 100%
- **Disponibilidad**: > 99.9%

### 8.2 Métricas de BigQuery

```sql
-- Query para métricas de memoria
SELECT
  DATE(created_at) as date,
  COUNT(*) as conversations_consolidated,
  AVG(turn_count) as avg_turns_per_session,
  COUNT(DISTINCT user_id) as active_users
FROM `genai-385616.corpchat.conversation_memory`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY date
ORDER BY date DESC;
```

---

## 9. Plan de Implementación

### 9.1 Fase 1: Infraestructura (1 día)
1. Crear tabla BigQuery `conversation_memory`
2. Configurar permisos IAM
3. Implementar `MemoryService` básico

### 9.2 Fase 2: Working Memory (0.5 días)
1. Implementar `get_working_memory`
2. Integrar en chat completions
3. Testing básico

### 9.3 Fase 3: Long-term Memory (1 día)
1. Implementar `get_long_term_memory`
2. Implementar consolidación automática
3. Testing de retrieval semántico

### 9.4 Fase 4: User Profile (0.5 días)
1. Implementar gestión de perfil
2. Integrar en contexto enriquecido
3. Testing de persistencia

### 9.5 Fase 5: Optimización (1 día)
1. Optimizar context window
2. Implementar métricas
3. Testing E2E completo

---

## 10. Conclusiones

### 10.1 Estrategia Recomendada

**Memoria Híbrida** que combine:
- ✅ **Working Memory** (Firestore) para contexto inmediato
- ✅ **Long-term Memory** (BigQuery) para retrieval histórico
- ✅ **User Profile** (Firestore) para contexto persistente
- ✅ **Consolidación automática** al finalizar sesiones

### 10.2 Ventajas

1. **Escalabilidad**: BigQuery maneja millones de conversaciones
2. **Performance**: Firestore para acceso rápido, BigQuery para búsqueda
3. **Flexibilidad**: Retrieval semántico con embeddings
4. **Costo**: Pay-per-use con BigQuery, Firestore para datos activos
5. **Integración**: Compatible con ADK y Open WebUI

### 10.3 Próximos Pasos

1. Implementar `MemoryService` en Gateway
2. Crear tabla BigQuery para memoria a largo plazo
3. Integrar en chat completions
4. Testing E2E con memoria híbrida
5. Monitoreo y optimización

---

**Documento preparado por**: AI Assistant  
**Revisión técnica**: Pendiente  
**Aprobación**: Pendiente
