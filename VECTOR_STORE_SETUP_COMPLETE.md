# ✅ BigQuery Vector Store - Implementación Completa

**Fecha**: 14 de octubre 2025  
**Decisión**: BigQuery como vector store nativo desde MVP  
**Justificación**: Búsqueda RAG sobre documentos adjuntos es el core value de CorpChat

---

## 🎯 **Decisión Arquitectónica**

### **¿Por qué BigQuery y no Firestore in-memory?**

| Aspecto | Firestore In-Memory | BigQuery Vector Search |
|---------|---------------------|------------------------|
| **Setup** | ✅ Simple | ⚠️ Requiere dataset/tabla |
| **Costo base** | ✅ $0 | ✅ $0 (pay-per-use) |
| **Escalabilidad** | ❌ Limitada (scope por chat) | ✅ Millones de vectores |
| **Latencia** | ⚠️ Aumenta con chunks | ✅ < 1s constante |
| **Búsqueda cross-chat** | ❌ No soportada | ✅ Nativa |
| **Migración futura** | ⚠️ Necesaria | ✅ Ya implementada |
| **Costo 1000 chats** | ~$1/mes (Firestore) | ~$2-5/mes (BigQuery) |

**Conclusión**: BigQuery desde día 1 para evitar migración futura.

---

## 📦 **Recursos Implementados**

### 1. Scripts de Infraestructura

✅ **`infra/scripts/audit_bigquery.sh`** - Auditoría pre-deployment
- Lista TODOS los datasets existentes (23 encontrados)
- Verifica colisiones de nombres
- Valida permisos de service account
- Genera reporte de seguridad

**Resultado auditoría**:
- ✅ Dataset `corpchat` NO existe (seguro crear)
- ✅ 0 colisiones detectadas
- ⚠️ SA necesita permisos BigQuery

✅ **`infra/scripts/setup_bigquery_vector_store.sh`** - Setup completo
- Crea dataset `corpchat` en `us-central1`
- Crea tabla `embeddings` con schema optimizado
- Particionamiento diario (auto-delete 30 días)
- Clustering por `user_id`, `chat_id`
- Asigna permisos a service account
- Crea view de debugging

### 2. Código Python

✅ **`services/agents/shared/bigquery_vector_search.py`**

**Clase**: `BigQueryVectorSearch`

**Métodos principales**:

```python
# Búsqueda semántica
search_similar_chunks(
    query_embedding: List[float],  # 768 dims
    chat_id: Optional[str] = None,  # Scope por chat o global
    top_k: int = 5,
    similarity_threshold: float = 0.7
) -> List[Dict]

# Inserción de chunks con embeddings
insert_chunks(
    chunks: List[Dict],
    ttl_days: Optional[int] = None  # 7 días dev, 30 prod
) -> bool

# Eliminación
delete_chunks_by_chat(chat_id: str) -> bool
delete_chunks_by_attachment(attachment_id: str) -> bool

# Estadísticas
get_stats(chat_id: Optional[str] = None) -> Dict
```

**Características**:
- ✅ Cosine similarity con `ML.DISTANCE`
- ✅ Parámetros dinámicos para seguridad SQL injection
- ✅ Logging estructurado
- ✅ Type hints completos
- ✅ Manejo de errores robusto
- ✅ TTL configurable por environment

### 3. Schema BigQuery

```sql
CREATE TABLE `genai-385616.corpchat.embeddings` (
  -- IDs
  chunk_id STRING NOT NULL,
  attachment_id STRING NOT NULL,
  chat_id STRING NOT NULL,
  user_id STRING NOT NULL,
  
  -- Contenido
  text STRING NOT NULL,
  embedding ARRAY<FLOAT64> NOT NULL,  -- 768 dims
  
  -- Metadata
  page INT64,
  source_filename STRING,
  chunk_index INT64,
  extraction_method STRING,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  expires_at TIMESTAMP  -- TTL
)
PARTITION BY DATE(created_at)
CLUSTER BY user_id, chat_id;
```

**Optimizaciones**:
- Particionamiento diario → queries solo escanean datos relevantes
- Clustering → reduce scan para queries por user/chat
- TTL automático → auto-limpieza de datos expirados

### 4. Integración

✅ Exportado en `services/agents/shared/__init__.py`  
✅ Agregado a `requirements.txt` (agents + ingestor)  
✅ Documentación inline completa

---

## 📊 **Arquitectura de Datos Final**

### **Firestore** (Metadata & Estado)

```yaml
corpchat_chats/{chatId}/
  ├── metadata (doc)
  │   ├── userId: string
  │   ├── title: string
  │   └── created_at: timestamp
  │
  └── corpchat_attachments/{attachmentId} (subcollection)
      ├── filename: string
      ├── mimeType: string
      ├── gcsPath: string
      ├── status: "processing" | "ready" | "failed"
      ├── chunks_count: int
      ├── uploaded_at: timestamp
      └── error_message?: string
```

**Propósito**: UI state, status tracking, ligero

### **BigQuery** (Vector Store)

```sql
corpchat.embeddings
  ├── chunk_id, attachment_id, chat_id, user_id
  ├── text (contenido)
  ├── embedding ARRAY<FLOAT64>[768]
  ├── metadata (page, source, method)
  └── timestamps (created_at, expires_at)
```

**Propósito**: Búsqueda semántica escalable

---

## 🔄 **Pipeline de Documentos → RAG**

```
1. Usuario adjunta documento → GCS Bucket
   ↓
2. Pub/Sub trigger → Ingestor Cloud Run
   ↓
3. Extractores → texto + metadata
   ↓
4. Chunking semántico → chunks 512-1024 tokens
   ↓
5. Embeddings Vertex AI → vectores (768 dims)
   ↓
6. Almacenamiento DUAL:
   ├── Firestore: metadata + status
   └── BigQuery: text + embeddings
   ↓
7. Búsqueda RAG:
   User query → embedding
   ↓
   BigQuery: SELECT con ML.DISTANCE
   ↓
   Top-K chunks → contexto para Gemini
   ↓
   Respuesta con citación
```

---

## 💰 **Costos Estimados**

### **Ejemplo: 1000 chats activos**

**Asunciones**:
- 50 documentos promedio por chat
- 200 chunks por documento  
- = 10M chunks total
- Tamaño por chunk: ~8KB (2KB text + 6KB embedding)

**Storage**:
```
10M chunks × 8KB = 80GB
80GB × $0.02/GB/mes = $1.60/mes
```

**Queries**:
```
100 búsquedas/día
Scan por query (con clustering): ~1MB
= 100 × 30 × 1MB = 3GB/mes escaneado
= 0.003TB × $5/TB = $0.015/mes
```

**Total estimado: ~$2/mes para 1000 chats activos** ✅

**Comparación**:
- Vertex AI Vector Search: ~$150-300/mes (costo fijo)
- BigQuery: ~$2-5/mes (pay-per-use) ← **83x más barato**

---

## ⏭️ **Próximos Pasos**

### 1. Ejecutar Setup BigQuery (5 min)

```bash
cd /Users/lufermalgo/Proyectos/CorpChat

# Hacer ejecutable
chmod +x infra/scripts/setup_bigquery_vector_store.sh

# Ejecutar
./infra/scripts/setup_bigquery_vector_store.sh
```

**Esto creará**:
- Dataset `genai-385616:corpchat`
- Tabla `embeddings` con schema completo
- View `embeddings_view` para debugging
- Permisos para `corpchat-app` SA

### 2. Verificar Recursos Creados

```bash
# Ver dataset
bq show genai-385616:corpchat

# Ver tabla
bq show genai-385616:corpchat.embeddings

# Ver schema
bq show --schema genai-385616:corpchat.embeddings

# Query de prueba
bq query --nouse_legacy_sql \
  'SELECT COUNT(*) as total FROM `genai-385616.corpchat.embeddings`'
```

### 3. Configurar IAP OAuth 2.0 (Manual)

**CRÍTICO para login con Google Workspace**

Ver guía completa en: (crear documento separado)

---

## 🧪 **Testing del Vector Store**

### Ejemplo de Uso

```python
from shared.bigquery_vector_search import BigQueryVectorSearch

# Inicializar
bq_search = BigQueryVectorSearch(project_id="genai-385616")

# Insertar chunks (después del ingestor)
chunks = [
    {
        'chunk_id': 'chunk_001',
        'attachment_id': 'att_abc',
        'chat_id': 'chat_123',
        'user_id': 'user_456',
        'text': 'Contenido del documento...',
        'embedding': [0.1, 0.2, ..., 0.8],  # 768 dims
        'page': 1,
        'source_filename': 'documento.pdf',
        'chunk_index': 0,
        'extraction_method': 'text'
    }
]

success = bq_search.insert_chunks(chunks, ttl_days=7)

# Búsqueda semántica
query_embedding = [0.15, 0.25, ...]  # 768 dims
results = bq_search.search_similar_chunks(
    query_embedding=query_embedding,
    chat_id='chat_123',
    top_k=5,
    similarity_threshold=0.7
)

for chunk in results:
    print(f"Similarity: {chunk['similarity']:.3f}")
    print(f"Text: {chunk['text'][:100]}...")
    print(f"Source: {chunk['source_filename']} (page {chunk['page']})")
    print("---")

# Estadísticas
stats = bq_search.get_stats(chat_id='chat_123')
print(f"Total chunks: {stats['total_chunks']}")
print(f"Total attachments: {stats['total_attachments']}")
```

---

## 📝 **Documentación Relacionada**

- `SHARED_PROJECT_SAFETY.md` - Seguridad proyecto compartido
- `AUDIT_SUMMARY_20251014.md` - Resultados auditoría GCP
- `GCP_SETUP_COMPLETE.md` - Setup GCP completado
- `audit_bigquery_YYYYMMDD.txt` - Reportes de auditoría BigQuery
- `docs/architecture.md` - Arquitectura completa
- Plan original: `corpchat-mvp-sprint-4-dias.plan.md`

---

## ✅ **Checklist de Completitud**

- [x] Script de auditoría BigQuery implementado
- [x] Auditoría ejecutada (0 colisiones)
- [x] Setup script creado
- [x] Clase `BigQueryVectorSearch` implementada
- [x] Schema de tabla diseñado
- [x] Particionamiento y clustering configurados
- [x] TTL implementado
- [x] Methods: search, insert, delete, stats
- [x] Integrado en shared module
- [x] Requirements.txt actualizados
- [x] Type hints completos
- [x] Logging estructurado
- [x] Documentación inline
- [x] Commits pushed a GitHub
- [ ] **BigQuery dataset/tabla creados** (pendiente ejecutar setup)
- [ ] **Permisos BigQuery asignados a SA** (pendiente)
- [ ] **Testing con datos reales** (pendiente ingestor)

---

## 🚀 **Status del Proyecto**

### Completado ✅

- ✅ Auditoría GCP (0 colisiones)
- ✅ Auditoría BigQuery (0 colisiones)
- ✅ Setup GCP (Firestore, GCS, Pub/Sub, SA, Secret)
- ✅ APIs habilitadas (incluyendo IAP)
- ✅ Estructura de proyecto completa
- ✅ Gateway OpenAI-compatible implementado
- ✅ Open WebUI con branding implementado
- ✅ ADK Orchestrator + 3 Specialists implementados
- ✅ Tool Servers (Docs + Sheets) implementados
- ✅ Firestore client con prefijos seguros
- ✅ **BigQuery Vector Store implementado** ⭐

### Pendiente ⏳

- ⏳ **Ejecutar setup_bigquery_vector_store.sh** (5 min)
- ⏳ **Configurar IAP OAuth 2.0** (10-15 min, manual)
- ⏳ Crear `.env` con variables
- ⏳ Deployment de servicios
- ⏳ Ingestor (extractores, chunking, embeddings)
- ⏳ Testing E2E

---

## 💡 **Decisiones Técnicas Clave**

1. **BigQuery desde MVP**: Evita migración futura, costo similar a in-memory
2. **Clustering por user_id, chat_id**: Optimiza queries más comunes
3. **Particionamiento diario**: Auto-cleanup, reduce costos
4. **TTL configurable**: 7 días dev, 30 días prod
5. **768 dims**: text-embedding-004 de Vertex AI
6. **Prefijos "corpchat"**: Seguridad en proyecto compartido

---

**Última actualización**: $(date)  
**Commits**: 3 (setup GCP, auditoría BQ, implementación vector store)  
**Status**: 🟢 LISTO PARA SETUP BIGQUERY

**Próxima acción**: `./infra/scripts/setup_bigquery_vector_store.sh`

