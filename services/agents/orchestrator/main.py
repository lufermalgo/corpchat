"""
Servidor HTTP para el orquestador - Versión MVP.

Expone endpoints para que el gateway pueda invocar al orquestador.
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
from google.cloud import logging as cloud_logging

# Agregar shared al path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from firestore_client import FirestoreClient

# Importar agente
from agent import root_agent

# Configurar logging
cloud_logging.Client().setup_logging()
_logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="CorpChat Orchestrator",
    description="Orquestador principal (MVP)",
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
        "version": "1.0.0-mvp",
        "status": "healthy"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Endpoint principal de chat.
    
    Args:
        request: Request de chat
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        Response del agente
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
            f"Chat request: user={user_id}, chat={request.chat_id}",
            extra={"user_id": user_id, "chat_id": request.chat_id}
        )
        
        # Invocar agente
        try:
            response_text = root_agent.chat(request.message, user_id)
            agent_name = "CorpChat"
            
        except Exception as e:
            _logger.error(f"Error invocando agente: {e}", exc_info=True)
            response_text = "Lo siento, hubo un error al procesar tu consulta. Por favor intenta de nuevo."
            agent_name = "CorpChat (fallback)"
        
        # Calcular métricas
        latency_ms = (time.time() - start_time) * 1000
        
        # Guardar en Firestore
        try:
            # Verificar si el chat existe
            chat = firestore_client.get_document(f"chats/{request.chat_id}")
            if not chat:
                # Crear chat
                firestore_client.set_document(
                    f"chats/{request.chat_id}",
                    {
                        "owner_id": user_id,
                        "title": "Nuevo Chat",
                        "created_at": firestore_client.get_server_timestamp(),
                        "updated_at": firestore_client.get_server_timestamp(),
                        "members": [user_id]
                    }
                )
            
            # Agregar mensaje del usuario
            firestore_client.set_document(
                f"chats/{request.chat_id}/messages/{int(time.time() * 1000)}_user",
                {
                    "role": "user",
                    "content": request.message,
                    "created_at": firestore_client.get_server_timestamp()
                }
            )
            
            # Agregar respuesta del asistente
            firestore_client.set_document(
                f"chats/{request.chat_id}/messages/{int(time.time() * 1000)}_assistant",
                {
                    "role": "assistant",
                    "content": response_text,
                    "agent": agent_name,
                    "latency_ms": latency_ms,
                    "created_at": firestore_client.get_server_timestamp()
                }
            )
            
        except Exception as e:
            _logger.error(f"Error guardando en Firestore: {e}", exc_info=True)
        
        return ChatResponse(
            response=response_text,
            agent_used=agent_name,
            latency_ms=latency_ms
        )
    
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        _logger.error(f"Error en chat endpoint: {e}", exc_info=True)
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
        # Obtener mensajes
        messages_collection = f"chats/{chat_id}/messages"
        messages = []
        
        # En Firestore, obtener subcolecc messages
        # (simplificado - en producción usar query ordenada)
        
        return {
            "chat_id": chat_id,
            "messages": messages,
            "count": len(messages)
        }
    
    except Exception as e:
        _logger.error(f"Error obteniendo historial: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    _logger.info(f"Iniciando orquestador en puerto {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
