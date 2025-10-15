"""
Servidor HTTP para el orquestador ADK.

Expone endpoints para que el gateway pueda invocar al orquestador.
Usa Google ADK Runner y run_async según documentación oficial:
https://google.github.io/adk-docs/runtime/
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional
import time

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import uvicorn

# Agregar parent directory al path para imports relativos
parent_path = Path(__file__).parent.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

# Importar desde shared package
from shared.firestore_client import FirestoreClient

# Importar ADK components
from google.adk.runners import InMemoryRunner
from google.genai import types

# Importar factory del agente (no el agente global)
from agent import create_orchestrator_agent, PROJECT_ID, LOCATION

# Configurar logging
_logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="CorpChat Orchestrator",
    description="Orquestador ADK usando Runner.run_async",
    version="1.0.0"
)

# Cliente Firestore
firestore_client = FirestoreClient()

# Cache del runner (lazy initialization)
_runner = None


def get_runner():
    """
    Lazy initialization del InMemoryRunner.
    Se crea bajo demanda para evitar timeout en container startup.
    
    Según patrón oficial de ADK:
    https://github.com/google/adk-python/blob/main/contributing/samples/hello_world/main.py
    """
    global _runner
    if _runner is None:
        _logger.info("🚀 Inicializando InMemoryRunner por primera vez...")
        orchestrator = create_orchestrator_agent()
        _runner = InMemoryRunner(
            agent=orchestrator,
            app_name="CorpChat"
        )
    return _runner


# Modelos Pydantic
class ChatRequest(BaseModel):
    """Request de chat al orquestador."""
    message: str
    chat_id: str
    user_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Response del orquestador."""
    response: str
    agent_used: str
    latency_ms: float
    events_processed: int


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "corpchat-orchestrator",
        "version": "1.0.0",
        "adk_runtime": "enabled",
        "model": os.getenv("MODEL", "gemini-2.5-flash-001"),
        "status": "healthy"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "adk": "enabled",
        "project": PROJECT_ID,
        "location": LOCATION
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Endpoint principal de chat usando ADK Runner.run_async.
    
    Según ADK docs: https://google.github.io/adk-docs/runtime/
    - Usar Runner para ejecutar agentes
    - run_async retorna un generador de eventos
    - Iterar con async for sobre los eventos
    - Procesar event.turn_complete para respuesta final
    
    Args:
        request: Request de chat
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        Response del agente ADK
    """
    start_time = time.time()
    
    try:
        # Determinar user ID
        user_id = request.user_id or "default"
        if x_goog_authenticated_user_email:
            # Extraer email del header IAP (formato: accounts.google.com:email@domain.com)
            if ":" in x_goog_authenticated_user_email:
                user_id = x_goog_authenticated_user_email.split(":")[-1]
        
        _logger.info(
            f"📨 Chat request: user={user_id}, chat={request.chat_id}, message_length={len(request.message)}"
        )
        
        # Obtener runner (lazy init)
        runner = get_runner()
        
        # Crear o obtener sesión existente
        # Según patrón oficial: usar runner.session_service
        try:
            session = await runner.session_service.get_session(
                app_name="CorpChat",
                user_id=user_id,
                session_id=request.chat_id
            )
        except Exception:
            # Si no existe, crear nueva sesión
            session = await runner.session_service.create_session(
                app_name="CorpChat",
                user_id=user_id,
                session_id=request.chat_id
            )
        
        # Variables para acumular respuesta
        response_text = ""
        events_processed = 0
        agent_name = "CorpChat (ADK)"
        
        # Convertir mensaje a types.Content según patrón oficial
        content = types.Content(
            role='user',
            parts=[types.Part.from_text(text=request.message)]
        )
        
        # Invocar ADK usando run_async según patrón oficial
        # Ref: https://github.com/google/adk-python/blob/main/contributing/samples/hello_world/main.py
        try:
            _logger.info(f"🔄 Iniciando ADK event loop...")
            
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=content
            ):
                events_processed += 1
                
                # Procesar evento: acumular texto de las partes
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
                            _logger.debug(f"📊 Event {events_processed} from {event.author}: {part.text[:50]}...")
            
            if not response_text:
                response_text = "Lo siento, no pude generar una respuesta."
                _logger.warning("⚠️ No se generó respuesta de ADK")
            
        except Exception as e:
            _logger.error(f"❌ Error en ADK event loop: {e}", exc_info=True)
            response_text = f"Lo siento, hubo un error al procesar tu consulta: {str(e)}"
            agent_name = "CorpChat (error)"
        
        # Calcular métricas
        latency_ms = (time.time() - start_time) * 1000
        
        # Guardar en Firestore
        try:
            # Verificar si el chat existe
            chat_path = f"corpchat_chats/{request.chat_id}"
            chat = firestore_client.get_document(chat_path)
            
            if not chat:
                # Crear chat
                firestore_client.set_document(
                    chat_path,
                    {
                        "owner_id": user_id,
                        "title": "Nuevo Chat",
                        "created_at": firestore_client.get_server_timestamp(),
                        "updated_at": firestore_client.get_server_timestamp(),
                        "members": [user_id]
                    }
                )
            
            # Agregar mensaje del usuario
            user_msg_path = f"{chat_path}/messages/{int(time.time() * 1000000)}_user"
            firestore_client.set_document(
                user_msg_path,
                {
                    "role": "user",
                    "content": request.message,
                    "created_at": firestore_client.get_server_timestamp()
                }
            )
            
            # Agregar respuesta del asistente
            assistant_msg_path = f"{chat_path}/messages/{int(time.time() * 1000000)}_assistant"
            firestore_client.set_document(
                assistant_msg_path,
                {
                    "role": "assistant",
                    "content": response_text,
                    "agent": agent_name,
                    "latency_ms": latency_ms,
                    "events_processed": events_processed,
                    "created_at": firestore_client.get_server_timestamp()
                }
            )
            
            _logger.info(f"✅ Mensajes guardados en Firestore")
            
        except Exception as e:
            _logger.error(f"❌ Error guardando en Firestore: {e}", exc_info=True)
        
        return ChatResponse(
            response=response_text,
            agent_used=agent_name,
            latency_ms=latency_ms,
            events_processed=events_processed
        )
    
    except HTTPException:
        raise
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        _logger.error(f"💥 Error en chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chats/{chat_id}/history")
async def get_history(
    chat_id: str,
    limit: int = 10
):
    """
    Obtiene el historial de un chat.
    
    Args:
        chat_id: ID del chat
        limit: Número máximo de mensajes
    
    Returns:
        Historial de mensajes
    """
    try:
        # Por ahora retornamos vacío
        # En producción, implementar query a Firestore
        
        return {
            "chat_id": chat_id,
            "messages": [],
            "count": 0
        }
    
    except Exception as e:
        _logger.error(f"Error obteniendo historial: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    
    _logger.info(f"🚀 Iniciando servidor FastAPI en puerto {port}")
    _logger.info(f"📊 ADK Runtime enabled")
    _logger.info(f"🌍 Proyecto: {PROJECT_ID}, Región: {LOCATION}")
    
    # Usar uvicorn con async support
    uvicorn.run(app, host="0.0.0.0", port=port)
