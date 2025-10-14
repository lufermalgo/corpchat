# Integración ADK en CorpChat

## Introducción

Este documento describe cómo se integra Google Genai ADK (Agent Development Kit) en CorpChat para crear un sistema multi-agente con orquestación inteligente.

## Referencias

- **ADK Repositorio**: https://github.com/google/adk-python
- **ADK Documentación**: https://google.github.io/adk-docs/
- **Repositorio local**: `references/adk-python-ref/`

## Arquitectura Multi-Agente

### Patrón: Coordinador con Especialistas

CorpChat utiliza el patrón de **agente coordinador** (root agent) que delega tareas a **agentes especialistas** (sub_agents) según la intención del usuario.

```python
from google.adk.agents import LlmAgent

# Agente coordinador (orquestador)
coordinator = LlmAgent(
    name="CorpChat Coordinator",
    model="gemini-2.5-flash-001",
    description="Coordino consultas corporativas y delego a especialistas",
    sub_agents=[
        conocimiento_empresa_agent,
        estado_tecnico_agent,
        productos_propuestas_agent
    ],
    tools=[docs_tool, sheets_tool]
)
```

### Flujo de Invocación

```
Usuario → Open WebUI → Gateway → Orquestador ADK
                                      │
                                      ├─→ ¿Consulta conocimiento? → Especialista Conocimiento
                                      ├─→ ¿Estado de sistemas? → Especialista Estado Técnico
                                      └─→ ¿Productos/cotización? → Especialista Productos
```

## Configuración de Agentes

### 1. Orquestador (Root Agent)

**Ubicación**: `services/agents/orchestrator/agent.py`

**Responsabilidades**:
- Análisis de intención del usuario
- Routing a especialista apropiado
- Gestión de sesión y contexto
- Agregación de respuestas

**Configuración**:

```python
# services/agents/orchestrator/agent.py
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
import os

# Importar especialistas
from specialists.conocimiento_empresa.agent import conocimiento_agent
from specialists.estado_tecnico.agent import estado_tecnico_agent
from specialists.productos_propuestas.agent import productos_agent

# Importar tools
from tools.docs_tool.tool import docs_tool
from tools.sheets_tool.tool import sheets_tool

root_agent = LlmAgent(
    name="CorpChat",
    model="gemini-2.5-flash-001",
    instruction="""
    Eres el asistente corporativo CorpChat. Tu misión es ayudar a los empleados con:
    
    1. Consultas sobre conocimiento interno de la empresa
    2. Estado de sistemas y monitoreo técnico
    3. Información de productos y generación de propuestas comerciales
    
    Analiza la consulta del usuario y delega al especialista apropiado.
    Siempre responde en español de manera profesional y concisa.
    """,
    description="Asistente corporativo que coordina especialistas",
    sub_agents=[
        conocimiento_agent,
        estado_tecnico_agent,
        productos_agent
    ],
    tools=[docs_tool, sheets_tool, google_search],
    thinking_config={
        "enabled": True,
        "budget_tokens": 1000
    }
)
```

**Thinking Mode**:

El orquestador usa thinking mode de Gemini 2.5 Flash para razonar sobre qué especialista invocar:

```python
thinking_config={
    "enabled": True,
    "budget_tokens": 1000  # Tokens dedicados a razonamiento interno
}
```

### 2. Especialista: Conocimiento Empresa

**Ubicación**: `services/agents/specialists/conocimiento_empresa/agent.py`

**Responsabilidades**:
- RAG sobre base de conocimiento corporativa
- Búsqueda semántica en Firestore
- Responder preguntas sobre políticas, procesos, historia

**Implementación**:

```python
from google.adk.agents import LlmAgent
from google.adk.tools import Tool
from shared.firestore_client import FirestoreClient

# Tool custom para búsqueda en KB
class KnowledgeSearchTool(Tool):
    def __init__(self):
        self.firestore = FirestoreClient()
    
    def search(self, query: str, top_k: int = 5):
        """Busca en la base de conocimiento corporativa."""
        # Generar embedding del query
        # Buscar chunks similares en Firestore
        # Retornar resultados rankeados
        pass

conocimiento_agent = LlmAgent(
    name="Especialista Conocimiento Empresa",
    model="gemini-2.5-flash-001",
    instruction="""
    Eres experto en el conocimiento interno de la empresa.
    Usa la base de conocimiento para responder preguntas sobre:
    - Políticas y procedimientos
    - Historia y cultura organizacional
    - Estructura y equipos
    - Procesos internos
    
    Siempre cita la fuente de la información.
    """,
    description="Experto en conocimiento interno de la empresa",
    tools=[KnowledgeSearchTool()]
)
```

### 3. Especialista: Estado Técnico

**Ubicación**: `services/agents/specialists/estado_tecnico/agent.py`

**Responsabilidades**:
- Consultar estado de sistemas via APIs de monitoreo
- Analizar logs y métricas
- Reportar incidents y alertas

**Implementación**:

```python
from google.adk.agents import LlmAgent
from google.adk.tools import Tool

class MonitoringTool(Tool):
    def get_system_status(self, system_name: str):
        """Consulta el estado de un sistema específico."""
        # Integrar con Splunk/Cloud Monitoring
        pass
    
    def get_recent_incidents(self, hours: int = 24):
        """Obtiene incidentes recientes."""
        pass

estado_tecnico_agent = LlmAgent(
    name="Especialista Estado Técnico",
    model="gemini-2.5-flash-001",
    instruction="""
    Eres experto en monitoreo y estado de sistemas.
    Consulta las herramientas de monitoreo para responder sobre:
    - Estado actual de servicios
    - Incidentes recientes
    - Métricas de rendimiento
    - Alertas activas
    
    Proporciona respuestas técnicas pero comprensibles.
    """,
    description="Experto en estado de sistemas y monitoreo",
    tools=[MonitoringTool()]
)
```

### 4. Especialista: Productos & Propuestas

**Ubicación**: `services/agents/specialists/productos_propuestas/agent.py`

**Responsabilidades**:
- Consultar catálogo de productos
- Generar cotizaciones
- Crear propuestas comerciales

**Implementación**:

```python
from google.adk.agents import LlmAgent
from tools.sheets_tool.tool import sheets_tool

productos_agent = LlmAgent(
    name="Especialista Productos y Propuestas",
    model="gemini-2.5-flash-001",
    instruction="""
    Eres experto en productos y generación de propuestas comerciales.
    Usa el catálogo de productos para:
    - Consultar información de productos y precios
    - Generar cotizaciones personalizadas
    - Crear propuestas comerciales
    - Comparar opciones para el cliente
    
    Siempre incluye precios actualizados y términos comerciales.
    """,
    description="Experto en productos y propuestas comerciales",
    tools=[sheets_tool]
)
```

## Tools (Herramientas)

### Docs Tool

**Propósito**: Leer documentos de GCS y Google Drive

```python
from google.adk.tools import Tool
from google.cloud import storage

class DocsTool(Tool):
    def read_document(self, path: str, user_id: str):
        """
        Lee un documento y retorna su contenido.
        
        Args:
            path: Ruta GCS o Drive ID
            user_id: ID del usuario solicitante (para validar permisos)
        
        Returns:
            Contenido del documento
        """
        # Validar permisos del usuario
        # Generar signed URL o leer directamente
        # Retornar contenido
        pass

docs_tool = DocsTool()
```

### Sheets Tool

**Propósito**: Leer rangos de Google Sheets

```python
from google.adk.tools import Tool
from googleapiclient.discovery import build

class SheetsTool(Tool):
    def read_range(self, spreadsheet_id: str, range_name: str):
        """
        Lee un rango de una Google Sheet.
        
        Args:
            spreadsheet_id: ID del spreadsheet
            range_name: Rango (ej: "A1:C10")
        
        Returns:
            Datos del rango
        """
        # Autenticar con service account
        # Leer rango
        # Cachear resultado
        pass

sheets_tool = SheetsTool()
```

## Gestión de Estado y Sesiones

### Sesiones en Firestore

```python
# shared/firestore_client.py
from google.cloud import firestore
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self):
        self.db = firestore.Client()
    
    def get_session(self, chat_id: str):
        """Recupera la sesión de un chat."""
        doc_ref = self.db.collection('chats').document(chat_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    
    def update_session(self, chat_id: str, data: dict):
        """Actualiza la sesión."""
        doc_ref = self.db.collection('chats').document(chat_id)
        doc_ref.set(data, merge=True)
    
    def get_history(self, chat_id: str, limit: int = 10):
        """Obtiene el historial de mensajes."""
        messages = self.db.collection('chats')\
            .document(chat_id)\
            .collection('messages')\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
        return [msg.to_dict() for msg in messages]
```

### Context Management

El orquestador mantiene contexto entre mensajes:

```python
def handle_request(user_message: str, chat_id: str, user_id: str):
    """Maneja un request del usuario."""
    
    # 1. Recuperar sesión
    session = session_manager.get_session(chat_id)
    history = session_manager.get_history(chat_id, limit=5)
    
    # 2. Invocar agente con contexto
    response = root_agent.run(
        prompt=user_message,
        context={
            "user_id": user_id,
            "chat_id": chat_id,
            "history": history,
            "session_state": session
        }
    )
    
    # 3. Actualizar sesión
    session_manager.update_session(chat_id, {
        "last_message": user_message,
        "last_response": response.text,
        "updated_at": datetime.now()
    })
    
    return response
```

## Deployment de Agentes

### Containerización

Cada agente se deploya como un servicio Cloud Run independiente:

```dockerfile
# services/agents/orchestrator/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Copiar shared
COPY ../shared /app/shared

# Exponer puerto
EXPOSE 8080

# Comando de inicio
CMD ["python", "main.py"]
```

### Cloud Run Config

```yaml
# services/agents/orchestrator/cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/${PROJECT_ID}/corpchat-orchestrator:${SHORT_SHA}'
      - '.'
  
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/${PROJECT_ID}/corpchat-orchestrator:${SHORT_SHA}'
  
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'corpchat-orchestrator'
      - '--image=gcr.io/${PROJECT_ID}/corpchat-orchestrator:${SHORT_SHA}'
      - '--region=us-central1'
      - '--platform=managed'
      - '--min-instances=0'
      - '--max-instances=5'
      - '--service-account=corpchat-app@${PROJECT_ID}.iam.gserviceaccount.com'
      - '--set-env-vars=PROJECT_ID=${PROJECT_ID}'
      - '--labels=team=corpchat,env=dev,service=orchestrator'
```

## Comunicación Gateway → Orquestador

### API del Orquestador

```python
# services/agents/orchestrator/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

app = FastAPI()
_logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    chat_id: str
    user_id: str

class ChatResponse(BaseModel):
    response: str
    agent_used: str
    tokens_used: int
    cost_estimate: float

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal de chat."""
    try:
        # Invocar root agent
        result = root_agent.run(
            prompt=request.message,
            context={
                "user_id": request.user_id,
                "chat_id": request.chat_id
            }
        )
        
        return ChatResponse(
            response=result.text,
            agent_used=result.agent_name,
            tokens_used=result.usage.total_tokens,
            cost_estimate=calculate_cost(result.usage)
        )
    
    except Exception as e:
        _logger.error(f"Error en chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### Gateway invocando Orquestador

```python
# services/gateway/app.py
import httpx

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://corpchat-orchestrator")

async def call_orchestrator(message: str, chat_id: str, user_id: str):
    """Llama al orquestador ADK."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ORCHESTRATOR_URL}/chat",
            json={
                "message": message,
                "chat_id": chat_id,
                "user_id": user_id
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
```

## Observabilidad

### Logging Estructurado

```python
import logging
from google.cloud import logging as cloud_logging

# Configurar Cloud Logging
cloud_logging.Client().setup_logging()

_logger = logging.getLogger(__name__)

def log_agent_invocation(agent_name: str, user_id: str, tokens: int, cost: float):
    """Log estructurado de invocación de agente."""
    _logger.info(
        "Agent invocation",
        extra={
            "agent_name": agent_name,
            "user_id": user_id,
            "tokens": tokens,
            "cost_usd": cost,
            "labels": {
                "service": "orchestrator",
                "team": "corpchat"
            }
        }
    )
```

### Métricas

- Invocaciones por agente
- Tokens consumidos por agente
- Latencia por especialista
- Tasa de acierto en routing

## Mejores Prácticas

1. **Instrucciones claras**: Definir rol y responsabilidades de cada agente explícitamente
2. **Tools focalizados**: Cada especialista solo tools relevantes a su dominio
3. **Context mínimo**: Pasar solo contexto necesario para reducir tokens
4. **Error handling**: Manejo robusto de errores en tools
5. **Rate limiting**: Implementar quotas por usuario y por agente
6. **Caching**: Cachear respuestas frecuentes cuando sea apropiado
7. **Monitoring**: Observabilidad end-to-end de todas las invocaciones

## Próximos Pasos

1. Implementar los agentes según este diseño
2. Crear tests unitarios por agente
3. Implementar tests de integración orquestador → especialistas
4. Definir métricas de calidad (accuracy, latencia, costo)
5. Optimizar instrucciones basándose en evaluaciones

## Referencias

- [ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Repository](https://github.com/google/adk-python)
- [Gemini 2.5 Flash](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)

