"""
Gateway OpenAI-compatible → Vertex AI Gemini

Este módulo implementa un gateway que expone una API compatible con OpenAI
y proxea las peticiones a Vertex AI Gemini con streaming.
"""

import logging
import os
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import httpx
from google.cloud import aiplatform
from google.cloud import logging as cloud_logging
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content
from vertexai.generative_models import ChatSession

# Configurar logging
cloud_logging.Client().setup_logging()
_logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
PROJECT_ID = os.getenv("VERTEX_PROJECT", "genai-385616")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL", "gemini-2.5-flash-001")

# Inicializar Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

app = FastAPI(
    title="CorpChat Gateway",
    description="OpenAI-compatible API → Vertex AI Gemini",
    version="1.0.0"
)


# Modelos Pydantic para requests/responses
class Message(BaseModel):
    """Mensaje en formato OpenAI."""
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """Request de chat completion compatible con OpenAI."""
    model: str = Field(default="gpt-4")
    messages: List[Message]
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2048)
    stream: Optional[bool] = Field(default=False)
    user: Optional[str] = None


class Usage(BaseModel):
    """Métricas de uso de tokens."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Choice(BaseModel):
    """Opción de respuesta."""
    index: int
    message: Message
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    """Response de chat completion compatible con OpenAI."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage


class Model(BaseModel):
    """Modelo disponible."""
    id: str
    object: str = "model"
    created: int
    owned_by: str = "google"


class ModelsResponse(BaseModel):
    """Lista de modelos disponibles."""
    object: str = "list"
    data: List[Model]


def extract_user_from_header(x_goog_authenticated_user_email: Optional[str] = None) -> str:
    """
    Extrae el user ID del header de IAP.
    
    Args:
        x_goog_authenticated_user_email: Header de IAP con email del usuario
    
    Returns:
        User ID (email sin el prefijo de IAP)
    """
    if not x_goog_authenticated_user_email:
        return "anonymous"
    
    # IAP header format: accounts.google.com:user@domain.com
    if ":" in x_goog_authenticated_user_email:
        return x_goog_authenticated_user_email.split(":")[-1]
    
    return x_goog_authenticated_user_email


def convert_messages_to_gemini(messages: List[Message]) -> List[Content]:
    """
    Convierte mensajes de formato OpenAI a formato Gemini.
    
    Args:
        messages: Lista de mensajes en formato OpenAI
    
    Returns:
        Lista de Content objects para Gemini
    """
    gemini_messages = []
    
    for msg in messages:
        role = "user" if msg.role in ["user", "system"] else "model"
        content = Content(
            role=role,
            parts=[Part.from_text(msg.content)]
        )
        gemini_messages.append(content)
    
    return gemini_messages


def estimate_tokens(text: str) -> int:
    """
    Estima el número de tokens en un texto.
    Aproximación: ~4 caracteres por token.
    
    Args:
        text: Texto a estimar
    
    Returns:
        Número estimado de tokens
    """
    return len(text) // 4


async def generate_stream(
    model: GenerativeModel,
    messages: List[Message],
    temperature: float,
    max_tokens: int,
    user_id: str
) -> AsyncGenerator[str, None]:
    """
    Genera respuestas en streaming desde Gemini.
    
    Args:
        model: Modelo de Gemini
        messages: Lista de mensajes
        temperature: Temperatura para generación
        max_tokens: Máximo de tokens a generar
        user_id: ID del usuario
    
    Yields:
        Chunks de respuesta en formato SSE (Server-Sent Events)
    """
    try:
        # Convertir mensajes
        gemini_messages = convert_messages_to_gemini(messages)
        
        # Configurar generación
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        # Generar con streaming
        chat = model.start_chat()
        
        # Enviar mensajes previos como contexto
        if len(gemini_messages) > 1:
            for content in gemini_messages[:-1]:
                chat.send_message(content.parts[0].text)
        
        # Último mensaje con streaming
        last_message = gemini_messages[-1].parts[0].text
        response_stream = chat.send_message(
            last_message,
            generation_config=generation_config,
            stream=True
        )
        
        chunk_id = f"chatcmpl-{datetime.now().timestamp()}"
        
        for chunk in response_stream:
            if chunk.text:
                # Formato OpenAI streaming
                data = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(datetime.now().timestamp()),
                    "model": MODEL_NAME,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": chunk.text},
                            "finish_reason": None
                        }
                    ]
                }
                yield f"data: {str(data)}\n\n"
        
        # Enviar mensaje de finalización
        data_done = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(datetime.now().timestamp()),
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }
        yield f"data: {str(data_done)}\n\n"
        yield "data: [DONE]\n\n"
        
        _logger.info(
            "Streaming completado",
            extra={
                "user_id": user_id,
                "model": MODEL_NAME,
                "labels": {"service": "gateway", "team": "corpchat"}
            }
        )
    
    except Exception as e:
        _logger.error(f"Error en streaming: {e}", exc_info=True)
        error_data = {
            "error": {
                "message": str(e),
                "type": "internal_error"
            }
        }
        yield f"data: {str(error_data)}\n\n"


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "corpchat-gateway", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """
    Lista los modelos disponibles (compatible con OpenAI).
    
    Returns:
        Lista de modelos disponibles
    """
    return ModelsResponse(
        object="list",
        data=[
            Model(
                id="gpt-4",
                created=int(datetime.now().timestamp()),
                owned_by="google"
            ),
            Model(
                id="gpt-3.5-turbo",
                created=int(datetime.now().timestamp()),
                owned_by="google"
            )
        ]
    )


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Endpoint de chat completions compatible con OpenAI.
    
    Args:
        request: Request de chat completion
        x_goog_authenticated_user_email: Header de IAP con email del usuario
    
    Returns:
        Response de chat completion o streaming
    """
    try:
        # Extraer user ID
        user_id = extract_user_from_header(x_goog_authenticated_user_email) or request.user or "anonymous"
        
        _logger.info(
            "Chat completion request",
            extra={
                "user_id": user_id,
                "model": request.model,
                "stream": request.stream,
                "messages_count": len(request.messages),
                "labels": {"service": "gateway", "team": "corpchat"}
            }
        )
        
        # Inicializar modelo
        model = GenerativeModel(MODEL_NAME)
        
        # Si es streaming
        if request.stream:
            return StreamingResponse(
                generate_stream(
                    model,
                    request.messages,
                    request.temperature,
                    request.max_tokens,
                    user_id
                ),
                media_type="text/event-stream"
            )
        
        # Si no es streaming
        gemini_messages = convert_messages_to_gemini(request.messages)
        
        generation_config = {
            "temperature": request.temperature,
            "max_output_tokens": request.max_tokens,
        }
        
        chat = model.start_chat()
        
        # Enviar mensajes previos
        if len(gemini_messages) > 1:
            for content in gemini_messages[:-1]:
                chat.send_message(content.parts[0].text)
        
        # Último mensaje
        last_message = gemini_messages[-1].parts[0].text
        response = chat.send_message(
            last_message,
            generation_config=generation_config
        )
        
        # Calcular tokens
        prompt_tokens = sum(estimate_tokens(msg.content) for msg in request.messages)
        completion_tokens = estimate_tokens(response.text)
        total_tokens = prompt_tokens + completion_tokens
        
        _logger.info(
            "Chat completion completado",
            extra={
                "user_id": user_id,
                "model": MODEL_NAME,
                "tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "labels": {"service": "gateway", "team": "corpchat"}
            }
        )
        
        # Formatear respuesta
        return ChatCompletionResponse(
            id=f"chatcmpl-{datetime.now().timestamp()}",
            created=int(datetime.now().timestamp()),
            model=MODEL_NAME,
            choices=[
                Choice(
                    index=0,
                    message=Message(role="assistant", content=response.text),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )
        )
    
    except Exception as e:
        _logger.error(f"Error en chat completion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global de excepciones.
    
    Args:
        request: Request que generó la excepción
        exc: Excepción capturada
    
    Returns:
        JSON response con el error
    """
    _logger.error(f"Excepción no manejada: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": str(exc),
                "type": "internal_error"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

