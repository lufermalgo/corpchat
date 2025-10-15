"""
Servidor HTTP para el orquestador ADK.

Expone endpoints para que el gateway pueda invocar al orquestador.
Usa Google ADK para orquestación multi-agente.
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

# Agregar shared al path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from firestore_client import FirestoreClient

# Importar agente ADK
from agent import root_agent

# Configurar logging
_logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="CorpChat Orchestrator",
    description="Orquestador ADK principal",
    version="1.0.0"
)

# Cliente Firestore
firestore_client = FirestoreClient()


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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "corpchat-orchestrator",
        "version": "1.0.0",
        "adk_enabled": root_agent is not None,
        "status": "healthy" if root_agent else "degraded"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    if root_agent is None:
        raise HTTPException(status_code=503, detail="Orchestrator agent not initialized")
    return {"status": "healthy", "adk": "enabled"}


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Endpoint principal de chat usando ADK.
    
    Args:
        request: Request de chat
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        Response del agente ADK
    """
    start_time = time.time()
    
    # Verificar que el agente esté inicializado
    if root_agent is None:
        raise HTTPException(
            status_code=503, 
            detail="Orchestrator agent not initialized. Check logs."
        )
    
    try:
        # Determinar user ID
        user_id = request.user_id or "default"
        if x_goog_authenticated_user_email:
            # Extraer email del header IAP (formato: accounts.google.com:email@domain.com)
            if ":" in x_goog_authenticated_user_email:
                user_id = x_goog_authenticated_user_email.split(":")[-1]
        
        _logger.info(
            f"Chat request: user={user_id}, chat={request.chat_id}, message_length={len(request.message)}",
            extra={"user_id": user_id, "chat_id": request.chat_id}
        )
        
        # Invocar agente ADK
        try:
            # ADK run method - ejecuta el agente con el mensaje
            # Según ADK docs, el método run() retorna un resultado
            response = root_agent.run(request.message)
            
            # Extraer texto de la respuesta
            # El formato puede variar, adaptarse según la respuesta real de ADK
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)
            
            agent_name = "CorpChat (ADK)"
            
        except Exception as e:
            _logger.error(f"Error invocando agente ADK: {e}", exc_info=True)
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
                    "created_at": firestore_client.get_server_timestamp()
                }
            )
            
            _logger.info(f"✅ Mensajes guardados en Firestore para chat {request.chat_id}")
            
        except Exception as e:
            _logger.error(f"❌ Error guardando en Firestore: {e}", exc_info=True)
        
        return ChatResponse(
            response=response_text,
            agent_used=agent_name,
            latency_ms=latency_ms
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
        # Obtener mensajes desde Firestore
        # Por simplicidad, retornamos vacío por ahora
        # En producción, implementar query ordenada
        
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
    
    if root_agent is None:
        _logger.error("❌ FATAL: Orchestrator agent not initialized. Cannot start server.")
        _logger.error("   Check logs above for initialization errors.")
        # Aún así iniciar el servidor para que Cloud Run no falle health check
        # Los requests fallarán con 503
    
    _logger.info(f"🚀 Iniciando servidor FastAPI en puerto {port}")
    _logger.info(f"📊 ADK Agent: {'✅ Enabled' if root_agent else '❌ Disabled'}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
