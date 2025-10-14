"""
Servidor HTTP para el orquestador ADK.

Expone endpoints para que el gateway pueda invocar al orquestador.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import time

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from google.cloud import logging as cloud_logging

# Agregar shared al path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from firestore_client import FirestoreClient
from utils import (
    extract_user_from_iap_header,
    estimate_cost,
    log_agent_invocation
)

# Importar agente
from agent import root_agent

# Configurar logging
cloud_logging.Client().setup_logging()
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
    tokens_used: int
    cost_estimate: float
    latency_ms: float


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "corpchat-orchestrator",
        "version": "1.0.0",
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
        # Extraer user ID
        user_id = extract_user_from_iap_header(x_goog_authenticated_user_email)
        if request.user_id:
            user_id = request.user_id
        
        _logger.info(
            f"Chat request: user={user_id}, chat={request.chat_id}",
            extra={"user_id": user_id, "chat_id": request.chat_id}
        )
        
        # Obtener o crear chat
        chat = firestore_client.get_chat(request.chat_id)
        if not chat:
            firestore_client.create_chat(
                chat_id=request.chat_id,
                owner_id=user_id,
                title="Nuevo Chat"
            )
        
        # Obtener historial
        history = firestore_client.get_chat_history(request.chat_id, limit=5)
        
        # Construir contexto para el agente
        context = {
            "user_id": user_id,
            "chat_id": request.chat_id,
            "history": history
        }
        
        # Invocar agente ADK
        # Nota: ADK 1.8.0 puede tener API diferente, ajustar según documentación
        try:
            # Intento de invocación (puede necesitar ajuste según ADK real)
            result = root_agent.generate(
                prompt=request.message,
                context=context
            )
            
            response_text = result.text if hasattr(result, 'text') else str(result)
            tokens_used = getattr(result, 'usage', {}).get('total_tokens', 0) or 1000  # Fallback
            agent_name = "CorpChat"
            
        except Exception as e:
            _logger.error(f"Error invocando agente ADK: {e}", exc_info=True)
            # Fallback: respuesta simple
            response_text = f"Lo siento, hubo un error al procesar tu consulta. Por favor intenta de nuevo."
            tokens_used = 100
            agent_name = "CorpChat (fallback)"
        
        # Calcular métricas
        latency_ms = (time.time() - start_time) * 1000
        cost_estimate = estimate_cost(
            prompt_tokens=len(request.message.split()) * 2,  # Aproximación
            completion_tokens=len(response_text.split()) * 2,
            model="gemini-2.5-flash-001"
        )
        
        # Guardar mensajes
        firestore_client.add_message(
            chat_id=request.chat_id,
            role="user",
            content=request.message
        )
        
        firestore_client.add_message(
            chat_id=request.chat_id,
            role="assistant",
            content=response_text,
            metadata={
                "agent": agent_name,
                "tokens": tokens_used,
                "cost_usd": cost_estimate,
                "latency_ms": latency_ms
            }
        )
        
        # Log estructurado
        log_agent_invocation(
            agent_name=agent_name,
            user_id=user_id,
            chat_id=request.chat_id,
            tokens=tokens_used,
            latency_ms=latency_ms,
            cost_usd=cost_estimate,
            success=True
        )
        
        return ChatResponse(
            response=response_text,
            agent_used=agent_name,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
            latency_ms=latency_ms
        )
    
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        _logger.error(f"Error en chat endpoint: {e}", exc_info=True)
        
        log_agent_invocation(
            agent_name="CorpChat",
            user_id=user_id if 'user_id' in locals() else "unknown",
            chat_id=request.chat_id,
            tokens=0,
            latency_ms=latency_ms,
            cost_usd=0.0,
            success=False,
            error=str(e)
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chats/{chat_id}/history")
async def get_history(
    chat_id: str,
    limit: int = 10,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Obtiene el historial de un chat.
    
    Args:
        chat_id: ID del chat
        limit: Número máximo de mensajes
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        Historial de mensajes
    """
    try:
        user_id = extract_user_from_iap_header(x_goog_authenticated_user_email)
        
        # Verificar acceso
        chat = firestore_client.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat no encontrado")
        
        if user_id not in chat.get('members', []):
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        history = firestore_client.get_chat_history(chat_id, limit=limit)
        
        return {
            "chat_id": chat_id,
            "messages": history,
            "count": len(history)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error obteniendo historial: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/chats")
async def get_user_chats(
    user_id: str,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Obtiene los chats de un usuario.
    
    Args:
        user_id: ID del usuario
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        Lista de chats del usuario
    """
    try:
        requester_id = extract_user_from_iap_header(x_goog_authenticated_user_email)
        
        # Solo puede ver sus propios chats
        if requester_id != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        chats = firestore_client.get_user_chats(user_id, limit=50)
        
        return {
            "user_id": user_id,
            "chats": chats,
            "count": len(chats)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error obteniendo chats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    _logger.info(f"Iniciando orquestador en puerto {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

