"""
Gateway OpenAI-compatible → Vertex AI Gemini

Este módulo implementa un gateway que expone una API compatible con OpenAI
y proxea las peticiones a Vertex AI Gemini con streaming.
"""

import json
import logging
import os
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Header, File, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import httpx
from google.cloud import aiplatform
from google.cloud import logging as cloud_logging
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content
from vertexai.generative_models import ChatSession
from model_selector import get_model_config, apply_model_config, get_capability_prompt
from google.cloud import firestore
from stt_service import STTService, LongDictationProcessor
from memory_service import MemoryService

# ==========================================
# CONFIGURACIÓN DE ENTORNO LOCAL
# ==========================================
IS_LOCAL = os.getenv("ENVIRONMENT", "production") == "local"

# URLs de servicios basadas en el entorno
if IS_LOCAL:
    INGESTOR_SERVICE_URL = "http://corpchat-ingestor:8080"
    SERVICE_NAME = "corpchat-gateway"
else:
    INGESTOR_SERVICE_URL = os.getenv("INGESTOR_SERVICE_URL", "https://corpchat-ingestor-36072227238.us-central1.run.app")
    SERVICE_NAME = os.getenv("SERVICE_NAME", "corpchat-gateway")


def extract_text_from_content(content: str | list[dict]) -> str:
    """
    Extrae texto de un contenido que puede ser string o lista multimodal.
    
    Args:
        content: Contenido del mensaje (string o lista de objetos con tipo text/image_url)
        
    Returns:
        Texto extraído del contenido
    """
    if isinstance(content, str):
        return content
    
    # Si es lista, extraer solo las partes de texto
    text_parts = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            text_parts.append(item.get("text", ""))
    
    return " ".join(text_parts)


def detect_re_read_command(user_message: str) -> Optional[dict]:
    """
    Detecta si el usuario está pidiendo re-leer un documento.
    
    Args:
        user_message: Mensaje del usuario
        
    Returns:
        Dict con información del comando o None si no es un comando de re-lectura
    """
    message_lower = user_message.lower()
    
    # Palabras clave para detectar comando de re-lectura
    re_read_keywords = [
        "re-lee", "relee", "lee de nuevo", "actualiza el contexto", 
        "revisa el archivo", "carga de nuevo", "procesa otra vez",
        "en el pasado te cargué", "archivo que subí", "documento anterior"
    ]
    
    if any(keyword in message_lower for keyword in re_read_keywords):
        # Extraer nombre del archivo si se menciona
        filename = None
        
        # Buscar patrones como "el archivo X" o "el documento Y"
        import re
        patterns = [
            r"archivo\s+([^.,!?]+)",
            r"documento\s+([^.,!?]+)", 
            r"archivo\s+que\s+([^.,!?]+)",
            r"documento\s+que\s+([^.,!?]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                filename = match.group(1).strip()
                break
        
        return {
            "command": "re_read",
            "filename": filename,
            "original_message": user_message
        }
    
    return None


async def save_conversation_to_firestore(user_id: str, session_id: str, turn_number: int, messages: list, response: str, model_used: str):
    """
    Guarda un turno de conversación en Firestore siguiendo mejores prácticas.
    Estructura jerárquica: corpchat_users/{user_id}/sesiones/{session_id}/turnos/{turn_id}
    
    Args:
        user_id: ID del usuario (email)
        session_id: ID de la sesión de chat
        turn_number: Número del turno en la conversación
        messages: Lista de mensajes de la conversación
        response: Respuesta del modelo
        model_used: Modelo utilizado
    """
    try:
        _logger.info(f"Guardando turno {turn_number} de conversación en Firestore para usuario: {user_id}")
        
        # Inicializar cliente de Firestore
        db = firestore.Client(project=PROJECT_ID)
        
        # ESTRUCTURA JERÁRQUICA SIGUIENDO MEJORES PRÁCTICAS:
        # corpchat_users/{user_id}/sesiones/{session_id}/turnos/{turn_id}
        
        # 1. Crear/actualizar documento del usuario
        users_collection = f"{FIRESTORE_COLLECTION_PREFIX}_users"
        user_ref = db.collection(users_collection).document(user_id)
        user_ref.set({
            "email": user_id,
            "last_activity": datetime.now().isoformat(),
            "total_sessions": firestore.Increment(1) if turn_number == 1 else firestore.Increment(0),
            "created_at": datetime.now().isoformat()
        }, merge=True)
        
        # 2. Crear/actualizar documento de sesión dentro del usuario
        session_ref = user_ref.collection("sesiones").document(session_id)
        session_ref.set({
            "session_id": session_id,
            "user_id": user_id,
            "last_turn": turn_number,
            "last_activity": datetime.now().isoformat(),
            "total_turns": turn_number,
            "created_at": datetime.now().isoformat()
        }, merge=True)
        
        # 3. Crear documento de turno dentro de la sesión
        turn_id = f"turn_{turn_number}_{int(datetime.now().timestamp())}"
        turn_ref = session_ref.collection("turnos").document(turn_id)
        
        turn_data = {
            "turn_id": turn_id,
            "turn_number": turn_number,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat()
                } for msg in messages
            ],
            "assistant_response": response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        turn_ref.set(turn_data)
        
        _logger.info(f"Turno {turn_number} guardado en Firestore con estructura jerárquica: {users_collection}/{user_id}/sesiones/{session_id}/turnos/{turn_id}")
        
    except Exception as e:
        _logger.error(f"Error guardando conversación en Firestore: {e}", exc_info=True)


def generate_session_id(user_id: str) -> str:
    """
    Genera un ID de sesión único para el usuario.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        ID de sesión único
    """
    import uuid
    timestamp = int(datetime.now().timestamp())
    return f"sess_{timestamp}_{str(uuid.uuid4())[:8]}"


async def get_next_turn_number(user_id: str, session_id: str) -> int:
    """
    Obtiene el siguiente número de turno para una sesión.
    
    Args:
        user_id: ID del usuario
        session_id: ID de la sesión
        
    Returns:
        Número del siguiente turno
    """
    try:
        db = firestore.Client(project=PROJECT_ID)
        session_ref = db.collection("corpchat_sessions").document(f"{user_id}_{session_id}")
        session_doc = session_ref.get()
        
        if session_doc.exists:
            session_data = session_doc.to_dict()
            return session_data.get("last_turn", 0) + 1
        else:
            return 1
            
    except Exception as e:
        _logger.error(f"Error obteniendo número de turno: {e}", exc_info=True)
        return 1


async def handle_re_read_command(user_id: str, command: dict) -> str:
    """
    Maneja el comando de re-lectura de documento.
    
    Args:
        user_id: ID del usuario
        command: Comando detectado
        
    Returns:
        Mensaje de respuesta
    """
    try:
        _logger.info(f"Manejando comando re-read para usuario: {user_id}")
        
        # Si no se especifica archivo, listar archivos disponibles
        if not command.get("filename"):
            # Llamar al endpoint de listar archivos
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{INGESTOR_SERVICE_URL}/files/{user_id}",
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    files = data.get("files", [])
                    
                    if not files:
                        return "No tienes archivos cargados. Puedes subir un archivo y luego pedirme que lo re-lea."
                    
                    # Crear lista de archivos disponibles
                    file_list = "\n".join([
                        f"- {file['filename']} (cargado el {file['created'][:10]})"
                        for file in files[:5]  # Mostrar solo los 5 más recientes
                    ])
                    
                    return f"""Tienes {data['files_count']} archivos cargados. Los más recientes son:

{file_list}

Para re-leer un archivo específico, puedes decir: "re-lee el archivo [nombre del archivo]" o "actualiza el contexto del archivo [nombre]"."""
                
                else:
                    return "No pude acceder a tus archivos en este momento. Inténtalo más tarde."
        
        # Re-leer archivo específico
        filename = command["filename"]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INGESTOR_SERVICE_URL}/re-read/{user_id}",
                params={"filename": filename, "force_refresh": True},
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return f"""✅ **Documento re-leído exitosamente**

He procesado nuevamente el archivo **{filename}** y actualizado el contexto con:
- {data['chunks_created']} chunks de información
- Tiempo de procesamiento: {data['processing_time']:.1f}s

Ahora puedes hacer preguntas específicas sobre este documento y tendré el contexto más actualizado."""
            
            elif response.status_code == 404:
                return f"No encontré el archivo **{filename}** en tus documentos cargados. Verifica el nombre del archivo."
            
            else:
                return f"Hubo un error al re-leer el archivo **{filename}**. Inténtalo más tarde."
    
    except Exception as e:
        _logger.error(f"Error manejando comando re-read: {e}", exc_info=True)
        return "Hubo un error al procesar tu solicitud. Inténtalo más tarde."


# Configurar logging
cloud_logging.Client().setup_logging()
_logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
# CONFIGURACIÓN DINÁMICA PARA MULTI-CLIENTE
PROJECT_ID = os.getenv("VERTEX_PROJECT", os.getenv("GOOGLE_CLOUD_PROJECT", "default-project"))
FIRESTORE_COLLECTION_PREFIX = os.getenv("FIRESTORE_COLLECTION_PREFIX", "corpchat")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL", "gemini-2.5-flash-001")

# Inicializar Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

app = FastAPI(
    title="CorpChat Gateway",
    description="OpenAI-compatible API → Vertex AI Gemini",
    version="1.0.0"
)


# Middleware removido - causaba errores en el request body
# La funcionalidad se manejará directamente en el endpoint


# Modelos Pydantic para requests/responses
class Message(BaseModel):
    """Mensaje en formato OpenAI."""
    role: str
    content: str | list[dict]  # Soporta texto + imágenes para modelos Gemini multimodales


class ChatCompletionRequest(BaseModel):
    """Request de chat completion compatible con OpenAI."""
    model: str = Field(default="gemini-2.5-flash", description="Modelo Gemini a usar (gemini-2.5-flash, gemini-1.5-pro, etc.)")
    messages: List[Message]
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Override temperature del modelo")
    max_tokens: Optional[int] = Field(default=None, description="Override max_tokens del modelo")
    stream: Optional[bool] = Field(default=False)
    user: Optional[str] = None
    session_id: Optional[str] = Field(default=None, description="ID de sesión para mantener contexto de conversación")
    chat_id: Optional[str] = Field(default=None, description="ID del chat para recuperar attachments")


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
    permission: list = []
    root: Optional[str] = None
    parent: Optional[str] = None
    supports_images: Optional[bool] = None
    supports_thinking: Optional[bool] = None
    supports_code: Optional[bool] = None


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
        _logger.warning("No se recibió header de autenticación IAP")
        return "anonymous"
    
    # IAP header format: accounts.google.com:user@domain.com
    if ":" in x_goog_authenticated_user_email:
        return x_goog_authenticated_user_email.split(":")[-1]
    
    return x_goog_authenticated_user_email


def convert_messages_to_gemini(messages: List[Message], chat_id: Optional[str] = None) -> List[Content]:
    """
    Convierte mensajes de formato OpenAI a formato Gemini.
    Soporta contenido multimodal (texto + imágenes) para TODOS los modelos Gemini.
    
    Args:
        messages: Lista de mensajes en formato OpenAI
        chat_id: ID del chat (opcional, para recuperar attachments)
    
    Returns:
        Lista de Content objects para Gemini
    """
    import base64
    gemini_messages = []
    
    _logger.info(f"🔄 Procesando {len(messages)} mensajes para Gemini")
    
    for i, msg in enumerate(messages):
        role = "user" if msg.role in ["user", "system"] else "model"
        parts = []
        
        _logger.info(f"📝 Mensaje {i+1}: role={msg.role}, content_type={type(msg.content)}")
        
        # Si el contenido es un string simple
        if isinstance(msg.content, str):
            _logger.info(f"📄 Contenido texto: {msg.content[:100]}...")
            parts.append(Part.from_text(msg.content))
        # Si es contenido multimodal (lista de objetos)
        elif isinstance(msg.content, list):
            _logger.info(f"🎨 Contenido multimodal con {len(msg.content)} elementos")
            for j, item in enumerate(msg.content):
                if isinstance(item, dict):
                    item_type = item.get("type")
                    _logger.info(f"  📋 Elemento {j+1}: type={item_type}")
                    
                    # Parte de texto
                    if item_type == "text":
                        text_content = item.get("text", "")
                        _logger.info(f"  📝 Texto: {text_content[:100]}...")
                        parts.append(Part.from_text(text_content))
                    
                    # Parte de imagen
                    elif item_type == "image_url":
                        image_url = item.get("image_url", {})
                        url = image_url.get("url", "") if isinstance(image_url, dict) else image_url
                        _logger.info(f"  🖼️ Imagen URL: {url[:50]}...")
                        
                        # Si la imagen está en base64 (formato: data:image/...;base64,...)
                        if url.startswith("data:"):
                            try:
                                # Extraer el mime type y los datos base64
                                header, data = url.split(",", 1)
                                mime_type = header.split(":")[1].split(";")[0]
                                image_bytes = base64.b64decode(data)
                                
                                # ESTRATEGIA ADK: Generar ID único para la imagen
                                import hashlib
                                image_hash = hashlib.md5(image_bytes).hexdigest()
                                image_id = f"img_{image_hash[:8]}"
                                
                                _logger.info(f"  ✅ Imagen base64 procesada: mime_type={mime_type}, size={len(image_bytes)} bytes, id={image_id}")
                                parts.append(Part.from_bytes(data=image_bytes, mime_type=mime_type))
                                
                                # Agregar referencia de imagen como texto (estrategia ADK)
                                parts.append(Part.from_text(f"[IMAGE-ID {image_id}]"))
                                
                            except Exception as e:
                                _logger.error(f"❌ Error procesando imagen base64: {e}")
                                parts.append(Part.from_text(f"[Error procesando imagen: {str(e)}]"))
                        
                        # Si es URL de GCS o path de attachment
                        elif url.startswith("gs://") or url.startswith("/api/files/"):
                            _logger.info(f"  🔗 Procesando imagen URL: {url}")
                            try:
                                # Importar AttachmentService
                                from attachment_service import AttachmentService
                                attachment_service = AttachmentService()
                                
                                # Obtener imagen desde GCS
                                image_bytes = attachment_service.process_image_url(url, chat_id)
                                
                                if image_bytes:
                                    # ESTRATEGIA ADK: Generar ID único para la imagen
                                    import hashlib
                                    image_hash = hashlib.md5(image_bytes).hexdigest()
                                    image_id = f"img_{image_hash[:8]}"
                                    
                                    # Determinar MIME type
                                    if url.startswith("/api/files/"):
                                        # Obtener metadata del attachment
                                        attachment_id = url.split("/")[-1]
                                        attachment_meta = attachment_service.get_attachment_metadata(chat_id, attachment_id)
                                        mime_type = attachment_service.get_image_mime_type(url, attachment_meta)
                                    else:
                                        mime_type = attachment_service.get_image_mime_type(url)
                                    
                                    _logger.info(f"  ✅ Imagen GCS procesada: mime_type={mime_type}, size={len(image_bytes)} bytes, id={image_id}")
                                    parts.append(Part.from_bytes(data=image_bytes, mime_type=mime_type))
                                    
                                    # Agregar referencia de imagen como texto (estrategia ADK)
                                    parts.append(Part.from_text(f"[IMAGE-ID {image_id}]"))
                                else:
                                    _logger.warning(f"  ⚠️ No se pudo obtener imagen de GCS")
                                    parts.append(Part.from_text("[Imagen no disponible]"))
                                    
                            except Exception as e:
                                _logger.error(f"❌ Error procesando imagen GCS: {e}")
                                parts.append(Part.from_text(f"[Error cargando imagen: {str(e)}]"))
                        else:
                            _logger.warning(f"⚠️ Formato de imagen no soportado: {url[:50]}...")
                            parts.append(Part.from_text(f"[Formato de imagen no soportado: {url}]"))
        
        if parts:
            content = Content(role=role, parts=parts)
            gemini_messages.append(content)
            _logger.info(f"✅ Mensaje {i+1} convertido con {len(parts)} partes")
        else:
            _logger.warning(f"⚠️ Mensaje {i+1} sin partes válidas")
    
    _logger.info(f"🎯 Total mensajes Gemini: {len(gemini_messages)}")
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
    user_id: str,
    model_config=None,
    chat_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Genera respuestas en streaming desde Gemini.
    
    Args:
        model: Modelo de Gemini
        messages: Lista de mensajes
        temperature: Temperatura para generación
        max_tokens: Máximo de tokens a generar
        user_id: ID del usuario
        model_config: Configuración del modelo seleccionado
    
    Yields:
        Chunks de respuesta en formato SSE (Server-Sent Events)
    """
    try:
        # Convertir mensajes
        gemini_messages = convert_messages_to_gemini(messages, chat_id)
        
        # Aplicar capacidades específicas del modelo al último mensaje si hay model_config
        if model_config and gemini_messages:
            last_message = gemini_messages[-1].parts[0].text
            enhanced_message = get_capability_prompt(model_config, last_message)
            # Crear nuevo Content con el mensaje mejorado
            from vertexai.generative_models import Part, Content
            enhanced_part = Part.from_text(enhanced_message)
            enhanced_content = Content(role="user", parts=[enhanced_part])
            gemini_messages[-1] = enhanced_content
        
        # Configurar generación
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        # Generar con streaming (deshabilitar validación de respuesta)
        chat = model.start_chat(response_validation=False)
        
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
                    "model": model_config.display_name if model_config else MODEL_NAME,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": chunk.text},
                            "finish_reason": None
                        }
                    ]
                }
                yield f"data: {json.dumps(data)}\n\n"
        
        # Enviar mensaje de finalización
        data_done = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(datetime.now().timestamp()),
            "model": model_config.display_name if model_config else MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }
        yield f"data: {json.dumps(data_done)}\n\n"
        yield "data: [DONE]\n\n"
        
        _logger.info(
            "Streaming completado",
            extra={
                "user_id": user_id,
                "model": model_config.display_name if model_config else MODEL_NAME,
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
    return {"status": "healthy", "service": SERVICE_NAME, "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/v1/admin/models")
async def get_admin_models():
    """Endpoint para administrar modelos dinámicamente."""
    from model_selector import AVAILABLE_MODELS
    
    return {
        "available_models": {
            model_id: {
                "display_name": config.display_name,
                "description": config.description,
                "gemini_model": config.gemini_model,
                "capability": config.capability.value,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "supports_thinking": config.supports_thinking,
                "supports_images": config.supports_images,
                "supports_code": config.supports_code
            }
            for model_id, config in AVAILABLE_MODELS.items()
        }
    }


@app.post("/v1/admin/models")
async def update_model_config(
    model_id: str,
    config: dict,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """Endpoint para actualizar configuración de modelos dinámicamente."""
    # TODO: Implementar actualización dinámica de modelos
    # Por ahora solo retornamos éxito
    return {"status": "success", "message": f"Model {model_id} updated"}


@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """
    Lista los modelos disponibles (compatible con OpenAI).
    Permite a Open WebUI mostrar selector de modelos con diferentes modos de pensamiento.
    
    Returns:
        Lista de modelos disponibles con configuración de thinking modes
    """
    from model_selector import get_models_endpoint
    models_data = get_models_endpoint()
    
    # Convertir a formato ModelsResponse incluyendo toda la información
    models = []
    for model_data in models_data["data"]:
        models.append(Model(
            id=model_data["id"],
            object=model_data.get("object", "model"),
            created=model_data["created"],
            owned_by=model_data["owned_by"],
            permission=model_data.get("permission", []),
            root=model_data.get("root"),
            parent=model_data.get("parent"),
            supports_images=model_data.get("supports_images"),
            supports_thinking=model_data.get("supports_thinking"),
            supports_code=model_data.get("supports_code")
        ))
    
    return ModelsResponse(
        object="list",
        data=models
    )


@app.get("/conversations/{user_id}")
async def get_user_conversations(user_id: str, limit: int = 10):
    """
    Lista las sesiones de conversación de un usuario específico usando estructura jerárquica.
    
    Args:
        user_id: ID del usuario
        limit: Número máximo de sesiones a retornar
        
    Returns:
        Lista de sesiones de conversación del usuario
    """
    try:
        _logger.info(f"Obteniendo sesiones para usuario: {user_id}")
        
        # Inicializar cliente de Firestore
        db = firestore.Client(project=PROJECT_ID)
        
        # Buscar sesiones del usuario usando estructura jerárquica
        users_collection = f"{FIRESTORE_COLLECTION_PREFIX}_users"
        user_ref = db.collection(users_collection).document(user_id)
        sessions_ref = user_ref.collection("sesiones")
        query = sessions_ref.order_by("last_activity", direction=firestore.Query.DESCENDING).limit(limit)
        
        sessions = []
        for doc in query.stream():
            session_data = doc.to_dict()
            sessions.append({
                "session_id": session_data.get("session_id"),
                "total_turns": session_data.get("total_turns", 0),
                "last_activity": session_data.get("last_activity"),
                "created_at": session_data.get("created_at")
            })
        
        _logger.info(f"Encontradas {len(sessions)} sesiones para usuario {user_id}")
        
        return {
            "user_id": user_id,
            "sessions_count": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        _logger.error(f"Error obteniendo sesiones del usuario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/conversations/{user_id}/{session_id}")
async def get_session_turns(user_id: str, session_id: str, limit: int = 20):
    """
    Lista los turnos de una sesión específica usando estructura jerárquica.
    
    Args:
        user_id: ID del usuario
        session_id: ID de la sesión
        limit: Número máximo de turnos a retornar
        
    Returns:
        Lista de turnos de la sesión
    """
    try:
        _logger.info(f"Obteniendo turnos de sesión {session_id} para usuario: {user_id}")
        
        # Inicializar cliente de Firestore
        db = firestore.Client(project=PROJECT_ID)
        
        # Buscar turnos de la sesión usando estructura jerárquica
        users_collection = f"{FIRESTORE_COLLECTION_PREFIX}_users"
        user_ref = db.collection(users_collection).document(user_id)
        session_ref = user_ref.collection("sesiones").document(session_id)
        turns_ref = session_ref.collection("turnos")
        query = turns_ref.order_by("turn_number", direction=firestore.Query.ASCENDING).limit(limit)
        
        turns = []
        for doc in query.stream():
            turn_data = doc.to_dict()
            turns.append({
                "turn_number": turn_data.get("turn_number"),
                "messages": turn_data.get("messages", []),
                "assistant_response": turn_data.get("assistant_response"),
                "model_used": turn_data.get("model_used"),
                "timestamp": turn_data.get("timestamp")
            })
        
        _logger.info(f"Encontrados {len(turns)} turnos para sesión {session_id}")
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "turns_count": len(turns),
            "turns": turns
        }
        
    except Exception as e:
        _logger.error(f"Error obteniendo turnos de la sesión: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/models", response_model=ModelsResponse)
async def list_models_legacy():
    """
    Endpoint legacy para compatibilidad con Open WebUI.
    Redirige al endpoint principal /v1/models.
    
    Returns:
        Lista de modelos disponibles
    """
    return await list_models()


async def enrich_messages_with_images(messages: List[Message], chat_id: Optional[str]) -> List[Message]:
    """
    Enriquece mensajes con imágenes usando estrategia ADK.
    Busca imágenes en GCS/Firestore y las agrega al contenido del mensaje.
    """
    enriched_messages = []
    
    for msg in messages:
        enriched_msg = msg.copy()
        
        # Solo procesar mensajes de usuario
        if msg.role == "user" and isinstance(msg.content, str) and chat_id:
            # Verificar si el mensaje menciona imágenes o attachments
            content_lower = msg.content.lower()
            if any(keyword in content_lower for keyword in ["imagen", "image", "adjunto", "attachment", "foto", "photo", "explica", "describe", "analiza", "qué", "que"]):
                _logger.info(f"🔍 Mensaje menciona imágenes, buscando attachments para chat {chat_id}")
                
                try:
                    from attachment_service import AttachmentService
                    attachment_service = AttachmentService()
                    
                    # Obtener attachments del chat
                    attachments = attachment_service.get_attachments_for_chat(chat_id)
                    _logger.info(f"📎 Encontrados {len(attachments)} attachments en chat {chat_id}")
                    
                    if attachments:
                        # Convertir a contenido multimodal
                        multimodal_content = []
                        
                        # Agregar texto original
                        multimodal_content.append({
                            "type": "text",
                            "text": msg.content
                        })
                        
                        # Agregar imágenes como URLs
                        for attachment in attachments:
                            if attachment.get("mime_type", "").startswith("image/"):
                                gcs_uri = attachment.get("gcs_uri")
                                if gcs_uri:
                                    _logger.info(f"🖼️ Agregando imagen: {gcs_uri}")
                                    multimodal_content.append({
                                        "type": "image_url",
                                        "image_url": {
                                            "url": gcs_uri
                                        }
                                    })
                        
                        if len(multimodal_content) > 1:  # Si hay imágenes además del texto
                            enriched_msg.content = multimodal_content
                            _logger.info(f"✅ Mensaje enriquecido con {len(multimodal_content)-1} imágenes")
                        else:
                            _logger.warning(f"⚠️ No se encontraron imágenes válidas en attachments")
                    else:
                        _logger.warning(f"⚠️ No se encontraron attachments para chat {chat_id}")
                        
                except Exception as e:
                    _logger.error(f"❌ Error enriqueciendo mensaje con imágenes: {e}")
        
        enriched_messages.append(enriched_msg)
    
    return enriched_messages


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    x_goog_authenticated_user_email: Optional[str] = Header(None),
    http_request: Request = None
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
        _logger.info(f"=== CHAT COMPLETIONS INICIADO ===")
        _logger.info(f"Request recibido: {len(request.messages)} mensajes")
        for i, msg in enumerate(request.messages):
            _logger.info(f"Mensaje {i}: role={msg.role}, content_type={type(msg.content)}")
        
        # Extraer user ID - MÚLTIPLES FUENTES DE AUTENTICACIÓN
        user_id = (
            extract_user_from_header(x_goog_authenticated_user_email) or  # IAP headers
            (http_request.headers.get("X-OpenWebUI-User-Email") if http_request else None) or  # Header de Open WebUI
            (http_request.headers.get("X-User-ID") if http_request else None) or  # Header personalizado
            request.user or  # Campo user del request
            "anonymous"
        )
        
        # Extraer chat_id - MÚLTIPLES FUENTES
        chat_id = (
            request.chat_id or  # Campo chat_id del request
            (http_request.headers.get("X-Chat-ID") if http_request else None) or  # Header de chat ID
            (http_request.headers.get("X-OpenWebUI-Chat-ID") if http_request else None) or  # Header de Open WebUI
            None
        )
        
        _logger.info(f"User ID: {user_id}, Chat ID: {chat_id}")
        
        # ESTRATEGIA ADK: Enriquecer mensajes con imágenes
        _logger.info("🔄 Aplicando estrategia ADK para enriquecer mensajes con imágenes")
        request.messages = await enrich_messages_with_images(request.messages, chat_id)
        
        # TEMPORAL: Si es anonymous, intentar extraer del contexto de Open WebUI
        if user_id == "anonymous":
            # Log detallado para debugging
            if http_request:
                _logger.warning(f"Usuario anonymous detectado. Headers recibidos:")
                _logger.warning(f"  X-OpenWebUI-User-Email: {http_request.headers.get('X-OpenWebUI-User-Email')}")
                _logger.warning(f"  X-OpenWebUI-User-Id: {http_request.headers.get('X-OpenWebUI-User-Id')}")
                _logger.warning(f"  X-User-ID: {http_request.headers.get('X-User-ID')}")
                _logger.warning(f"  Authorization: {http_request.headers.get('Authorization')}")
                _logger.warning(f"  User-Agent: {http_request.headers.get('User-Agent')}")
                _logger.warning(f"  Referer: {http_request.headers.get('Referer')}")
            _logger.warning(f"X-Goog-Authenticated-User-Email: {x_goog_authenticated_user_email}")
            _logger.warning(f"Request user: {request.user}")
            
            # SOLUCIÓN TEMPORAL: Usar un identificador más descriptivo para anonymous
            # En producción, esto debería resolverse con IAP o headers de Open WebUI
            user_id = f"anonymous_{int(datetime.now().timestamp())}"
            
            _logger.warning(f"Usuario final asignado: {user_id}")
        
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
        
        # Obtener configuración del modelo seleccionado
        model_config = get_model_config(request.model)
        
        _logger.info(
            f"Using Gemini model: {model_config.display_name} ({model_config.capability.value})",
            extra={
                "user_id": user_id,
                "selected_model": request.model,
                "gemini_model": model_config.gemini_model,
                "capability": model_config.capability.value,
                "supports_thinking": model_config.supports_thinking,
                "supports_images": model_config.supports_images,
                "supports_code": model_config.supports_code,
                "labels": {"service": "gateway", "team": "corpchat"}
            }
        )
        
        # Obtener el último mensaje del usuario (extraer texto si es multimodal)
        user_message = extract_text_from_content(request.messages[-1].content) if request.messages else ""
        
        # DETECCIÓN DE COMANDOS ESPECIALES
        re_read_command = detect_re_read_command(user_message)
        if re_read_command:
            _logger.info(f"Comando re-read detectado: {re_read_command}")
            
            # Manejar comando de re-lectura
            command_response = await handle_re_read_command(user_id, re_read_command)
            
            # Retornar respuesta inmediata del comando
            return {
                "id": f"chatcmpl-{int(datetime.now().timestamp())}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": command_response
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        
        # DEFINIR SESSION_ID ANTES DE USARLO
        # TEMPORAL: Para usuarios anonymous, usar un session_id fijo por IP
        if user_id.startswith("anonymous_"):
            # Extraer IP del request para crear session_id persistente
            client_ip = http_request.client.host if http_request else "unknown"
            session_id = f"anon_session_{hash(client_ip) % 10000}"
            _logger.info(f"Session ID para usuario anonymous: {session_id} (IP: {client_ip})")
        else:
            # Para usuarios reales, usar session_id del request o generar uno
            session_id = request.session_id if request.session_id else generate_session_id(user_id)
        
        # MEMORIA: Enriquecer contexto con memoria a corto y largo plazo
        enhanced_context = await memory_service.enrich_context(
            user_id=user_id,
            session_id=session_id,
            current_query=user_message
        )
        
        # RAG: Buscar información relevante en embeddings
        rag_context = ""
        try:
            
            if user_message:
                _logger.info(f"Realizando búsqueda RAG para: {user_message[:100]}...")
                
                # Generar embedding de la consulta usando Vertex AI
                import vertexai
                from vertexai.language_models import TextEmbeddingModel
                
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
                location = os.getenv("GOOGLE_CLOUD_LOCATION")
                if not project_id or not location:
                    raise ValueError("GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION environment variables are required")
                vertexai.init(project=project_id, location=location)
                embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
                embeddings = embedding_model.get_embeddings([user_message])
                query_embedding = embeddings[0].values
                
                # Buscar en BigQuery usando SQL
                from google.cloud import bigquery
                
                client = bigquery.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
                table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.corpchat.embeddings"
                
                # Query SQL para búsqueda de similitud
                query = f"""
                SELECT text, source_filename, chunk_index, 
                       ML.DISTANCE(embedding, @query_embedding, 'COSINE') as distance
                FROM `{table_id}`
                WHERE ML.DISTANCE(embedding, @query_embedding, 'COSINE') < 0.3
                ORDER BY ML.DISTANCE(embedding, @query_embedding, 'COSINE') ASC
                LIMIT 3
                """
                
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding)
                    ]
                )
                
                query_job = client.query(query, job_config=job_config)
                results = query_job.result()
                
                # Convertir resultados al formato esperado
                results = [
                    {
                        "text": row.text,
                        "source_filename": row.source_filename,
                        "chunk_index": row.chunk_index,
                        "distance": row.distance
                    }
                    for row in results
                ]
                
                if results:
                    _logger.info(f"Encontrados {len(results)} resultados RAG")
                    rag_context = "\n\n".join([
                        f"Fuente: {result['source_filename']} (chunk {result['chunk_index']})\n{result['text']}"
                        for result in results
                    ])
                    _logger.info(f"Contexto RAG: {len(rag_context)} caracteres")
                else:
                    _logger.info("No se encontraron resultados RAG")
                    
        except Exception as e:
            _logger.error(f"Error en búsqueda RAG: {e}", exc_info=True)
        
        # Configuración de generación con override del usuario o configuración del modelo
        generation_config = {
            "temperature": request.temperature if request.temperature is not None else model_config.temperature,
            "max_output_tokens": request.max_tokens if request.max_tokens is not None else model_config.max_tokens,
        }
        
        # Inicializar modelo Gemini con configuración específica
        model = GenerativeModel(model_config.gemini_model)
        
        # Si es streaming
        if request.stream:
            return StreamingResponse(
                generate_stream(
                    model,
                    request.messages,
                    generation_config["temperature"],
                    generation_config["max_output_tokens"],
                    user_id,
                    model_config,
                    chat_id
                ),
                media_type="text/event-stream"
            )
        
        # Si no es streaming
        gemini_messages = convert_messages_to_gemini(request.messages, chat_id)
        
        # Aplicar capacidades específicas del modelo al último mensaje
        if gemini_messages:
            last_message = gemini_messages[-1].parts[0].text
            
            # Combinar contexto enriquecido con RAG
            full_context = ""
            if enhanced_context:
                full_context += f"CONTEXTO DE MEMORIA:\n{enhanced_context}\n\n"
            if rag_context:
                full_context += f"INFORMACIÓN RELEVANTE DE DOCUMENTOS:\n{rag_context}\n\n"
            
            enhanced_message = get_capability_prompt(model_config, last_message)
            if full_context:
                enhanced_message = f"{full_context}{enhanced_message}"
            
            # Crear nuevo Content con el mensaje mejorado
            from vertexai.generative_models import Part, Content
            enhanced_part = Part.from_text(enhanced_message)
            enhanced_content = Content(role="user", parts=[enhanced_part])
            gemini_messages[-1] = enhanced_content
        
        # Agregar contexto RAG si está disponible
        if rag_context:
            from vertexai.generative_models import Part, Content
            rag_part = Part.from_text(f"\n\nInformación relevante de documentos:\n{rag_context}")
            rag_content = Content(role="user", parts=[rag_part])
            gemini_messages.append(rag_content)
        
        chat = model.start_chat(response_validation=False)
        
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
        
        # Calcular tokens (extraer texto si es multimodal)
        prompt_tokens = sum(estimate_tokens(extract_text_from_content(msg.content)) for msg in request.messages)
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
        
        # GUARDAR CONVERSACIÓN EN FIRESTORE
        
        turn_number = await get_next_turn_number(user_id, session_id)
        
        await save_conversation_to_firestore(
            user_id=user_id,
            session_id=session_id,
            turn_number=turn_number,
            messages=request.messages,
            response=response.text,
            model_used=request.model
        )
        
        # CONSOLIDAR MEMORIA (cada 10 turnos o al final de sesión)
        if turn_number % 10 == 0:
            try:
                consolidation_result = await memory_service.consolidate_session_memory(user_id, session_id)
                _logger.info(f"Memoria consolidada: {consolidation_result}")
            except Exception as e:
                _logger.error(f"Error consolidando memoria: {e}", exc_info=True)
        
        # Formatear respuesta
        return ChatCompletionResponse(
            id=f"chatcmpl-{datetime.now().timestamp()}",
            created=int(datetime.now().timestamp()),
            model=request.model,  # Usar modelo seleccionado por el usuario
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


@app.post("/chat/completions")
async def chat_completions_legacy(
    request: ChatCompletionRequest,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Endpoint legacy de chat completions para compatibilidad con Open WebUI.
    Redirige al endpoint principal /v1/chat/completions.
    
    Args:
        request: Request de chat completion
        x_goog_authenticated_user_email: Email del usuario autenticado
        
    Returns:
        Respuesta de chat completion
    """
    return await chat_completions(request, x_goog_authenticated_user_email)


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


# Inicializar servicio STT
stt_service = STTService()
long_dictation_processor = LongDictationProcessor()
memory_service = MemoryService(PROJECT_ID)


@app.post("/v1/audio/transcriptions")
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),  # OpenAI compatible
    language: str = Form("es"),
    response_format: str = Form("json"),
    temperature: float = Form(0.0),
    http_request: Request = None
):
    """
    Endpoint compatible con OpenAI Whisper API.
    Utiliza Google Cloud Speech-to-Text internamente.
    
    Args:
        file: Archivo de audio (WAV, MP3, FLAC, etc.)
        model: Modelo (siempre "whisper-1" para compatibilidad)
        language: Código de idioma (es, en, pt)
        response_format: Formato de respuesta (json)
        temperature: Temperatura (no usado en Speech-to-Text)
    
    Returns:
        Transcripción en formato OpenAI-compatible
    """
    try:
        _logger.info(
            f"🎤 Transcripción de audio iniciada",
            extra={
                "audio_filename": file.filename,
                "content_type": file.content_type,
                "language": language,
                "model": model,
                "labels": {"service": "gateway", "team": "corpchat"}
            }
        )
        
        # Leer contenido del archivo
        audio_content = await file.read()
        
        # Detectar formato de audio
        audio_info = stt_service.detect_audio_format(audio_content)
        _logger.info(f"📊 Información del audio: {audio_info}")
        
        if not audio_info["is_supported"]:
            _logger.warning(f"⚠️ Formato de audio no soportado: {audio_info['format']}")
            # Continuar de todas formas, Speech-to-Text puede manejar más formatos
        
        # Mapear código de idioma
        language_map = {
            "es": "es-ES",
            "en": "en-US", 
            "pt": "pt-BR",
            "fr": "fr-FR",
            "de": "de-DE",
            "it": "it-IT",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "zh": "zh-CN",
            "zh-tw": "zh-TW"
        }
        language_code = language_map.get(language.lower(), "es-ES")
        
        _logger.info(f"🌍 Idioma detectado: {language} -> {language_code}")
        
        # Transcribir usando Google Cloud Speech-to-Text
        result = await stt_service.transcribe_audio(
            audio_content=audio_content,
            language_code=language_code,
            enable_automatic_punctuation=True,
            enable_word_confidence=True
        )
        
        if "error" in result:
            _logger.error(f"❌ Error en transcripción: {result['error']}")
            raise HTTPException(status_code=500, detail=f"Error en transcripción: {result['error']}")
        
        # Formato OpenAI-compatible
        response_data = {
            "text": result["transcript"],
            "language": language_code,
            "duration": None,  # Speech-to-Text no proporciona duración
            "words": [
                {
                    "word": word["word"],
                    "start": word.get("start_time"),
                    "end": word.get("end_time"),
                    "probability": word.get("confidence")
                }
                for word in result.get("words", [])
            ] if result.get("words") else None
        }
        
        _logger.info(
            f"✅ Transcripción completada",
            extra={
                "transcript_length": len(result["transcript"]),
                "confidence": result["confidence"],
                "language": language_code,
                "words_count": len(result.get("words", [])),
                "labels": {"service": "gateway", "team": "corpchat"}
            }
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"❌ Error en transcripción: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.get("/v1/audio/models")
async def list_audio_models():
    """
    Lista modelos de audio disponibles (compatible con OpenAI).
    
    Returns:
        Lista de modelos soportados
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "whisper-1",
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai-internal"
            }
        ]
    }


@app.get("/v1/audio/languages")
async def list_supported_languages():
    """
    Lista idiomas soportados para transcripción.
    
    Returns:
        Lista de idiomas disponibles
    """
    return stt_service.get_supported_languages()


@app.get("/v1/audio/models/stt")
async def list_stt_models():
    """
    Lista modelos específicos de Speech-to-Text disponibles.
    
    Returns:
        Lista de modelos STT con descripciones
    """
    return stt_service.get_available_models()


@app.post("/stt/transcribe")
async def transcribe_audio_public(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: str = Form("es")
):
    """
    Endpoint público para transcripción de audio.
    Utilizado por Open WebUI para STT sin autenticación.
    """
    try:
        _logger.info(
            f"🎤 Transcripción pública de audio iniciada",
            extra={
                "audio_filename": file.filename,
                "content_type": file.content_type,
                "language": language,
                "model": model,
                "labels": {"service": "gateway", "team": "corpchat", "endpoint": "public_stt"}
            }
        )
        
        # Leer contenido del archivo
        audio_content = await file.read()
        
        # Detectar formato de audio
        audio_info = stt_service.detect_audio_format(audio_content)
        _logger.info(f"📊 Información del audio: {audio_info}")
        
        if not audio_info["is_supported"]:
            _logger.warning(f"⚠️ Formato de audio no soportado: {audio_info['format']}")
        
        # Mapear código de idioma
        language_map = {
            "es": "es-ES",
            "en": "en-US",
            "pt": "pt-BR",
            "fr": "fr-FR",
            "de": "de-DE",
            "it": "it-IT",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "zh": "zh-CN"
        }
        language_code = language_map.get(language.lower(), "es-ES")
        _logger.info(f"🌍 Idioma detectado: {language} -> {language_code}")
        
        # Transcribir usando Google Cloud Speech-to-Text
        result = await stt_service.transcribe_audio(
            audio_content=audio_content,
            language_code=language_code,
            enable_automatic_punctuation=True,
            enable_word_confidence=True
        )
        
        # Formato OpenAI-compatible
        response = {
            "text": result.get("transcript", ""),
            "confidence": result.get("confidence", 0.0),
            "language": language_code,
            "model": model
        }
        
        _logger.info(
            f"✅ Transcripción completada exitosamente",
            extra={
                "transcript_length": len(result.get("transcript", "")),
                "confidence": result.get("confidence", 0.0),
                "language": language_code,
                "labels": {"service": "gateway", "team": "corpchat", "endpoint": "public_stt"}
            }
        )
        
        return response
        
    except Exception as e:
        _logger.error(f"❌ Error en transcripción pública: {e}", exc_info=True)
        return {"error": f"Error en transcripción: {str(e)}", "text": ""}


@app.post("/v1/audio/transcriptions-long")
async def transcribe_long_dictation(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: str = Form("es")
):
    """
    Endpoint especializado para dictados largos (hasta 10 minutos).
    Utiliza LongDictationProcessor para manejo optimizado.
    """
    try:
        _logger.info(
            f"🎤 Dictado largo iniciado",
            extra={
                "audio_filename": file.filename,
                "content_type": file.content_type,
                "language": language,
                "model": model,
                "labels": {"service": "gateway", "team": "corpchat", "endpoint": "long_dictation"}
            }
        )
        
        # Leer contenido del archivo
        audio_content = await file.read()
        
        # Mapear código de idioma
        language_map = {
            "es": "es-ES",
            "en": "en-US",
            "pt": "pt-BR",
            "fr": "fr-FR",
            "de": "de-DE",
            "it": "it-IT",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "zh": "zh-CN"
        }
        language_code = language_map.get(language.lower(), "es-ES")
        
        # Obtener información de procesamiento
        processing_info = await long_dictation_processor.get_processing_info(audio_content)
        _logger.info(f"📊 Información de procesamiento: {processing_info}")
        
        # Verificar si se puede procesar
        if not processing_info["can_process"]:
            _logger.warning(f"⚠️ Dictado demasiado largo: {processing_info['duration_seconds']:.1f}s")
            return {
                "error": "Audio demasiado largo",
                "message": "El dictado no puede exceder 10 minutos. Por favor, divide tu mensaje en partes más cortas.",
                "max_duration": 600,
                "duration_seconds": processing_info["duration_seconds"]
            }
        
        # Procesar dictado largo
        result = await long_dictation_processor.process_long_dictation(
            audio_content=audio_content,
            language_code=language_code
        )
        
        # Formato OpenAI-compatible
        response = {
            "text": result.get("transcript", ""),
            "processing_info": processing_info,
            "confidence": result.get("confidence", 0.0),
            "method": result.get("method", "unknown")
        }
        
        _logger.info(
            f"✅ Dictado largo completado exitosamente",
            extra={
                "transcript_length": len(result.get("transcript", "")),
                "confidence": result.get("confidence", 0.0),
                "language": language_code,
                "strategy": processing_info["strategy"],
                "labels": {"service": "gateway", "team": "corpchat", "endpoint": "long_dictation"}
            }
        )
        
        return response
        
    except Exception as e:
        _logger.error(f"❌ Error en dictado largo: {e}", exc_info=True)
        return {"error": f"Error en transcripción: {str(e)}", "text": ""}


@app.post("/v1/audio/transcriptions-public")
async def transcribe_audio_public_openai(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: str = Form("es")
):
    """
    Endpoint público para transcripción de audio (OpenAI compatible).
    Utilizado por Open WebUI para STT sin autenticación.
    """
    try:
        _logger.info(
            f"🎤 Transcripción pública OpenAI de audio iniciada",
            extra={
                "audio_filename": file.filename,
                "content_type": file.content_type,
                "language": language,
                "model": model,
                "labels": {"service": "gateway", "team": "corpchat", "endpoint": "public_openai_stt"}
            }
        )
        
        # Leer contenido del archivo
        audio_content = await file.read()
        
        # Detectar formato de audio
        audio_info = stt_service.detect_audio_format(audio_content)
        _logger.info(f"📊 Información del audio: {audio_info}")
        
        if not audio_info["is_supported"]:
            _logger.warning(f"⚠️ Formato de audio no soportado: {audio_info['format']}")
        
        # Mapear código de idioma
        language_map = {
            "es": "es-ES",
            "en": "en-US",
            "pt": "pt-BR",
            "fr": "fr-FR",
            "de": "de-DE",
            "it": "it-IT",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "zh": "zh-CN"
        }
        language_code = language_map.get(language.lower(), "es-ES")
        _logger.info(f"🌍 Idioma detectado: {language} -> {language_code}")
        
        # Transcribir usando Google Cloud Speech-to-Text
        result = await stt_service.transcribe_audio(
            audio_content=audio_content,
            language_code=language_code,
            enable_automatic_punctuation=True,
            enable_word_confidence=True
        )
        
        # Formato OpenAI-compatible (solo "text")
        response = {
            "text": result.get("transcript", "")
        }
        
        _logger.info(
            f"✅ Transcripción pública OpenAI completada exitosamente",
            extra={
                "transcript_length": len(result.get("transcript", "")),
                "confidence": result.get("confidence", 0.0),
                "language": language_code,
                "labels": {"service": "gateway", "team": "corpchat", "endpoint": "public_openai_stt"}
            }
        )
        
        return response
        
    except Exception as e:
        _logger.error(f"❌ Error en transcripción pública OpenAI: {e}", exc_info=True)
        return {"error": f"Error en transcripción: {str(e)}", "text": ""}


@app.post("/v1/memory/consolidate/{user_id}/{session_id}")
async def consolidate_memory_endpoint(user_id: str, session_id: str):
    """
    Endpoint para consolidar memoria de una sesión específica.
    
    Args:
        user_id: ID del usuario
        session_id: ID de la sesión
    
    Returns:
        Resultado de la consolidación
    """
    try:
        _logger.info(f"Consolidando memoria para usuario {user_id}, sesión {session_id}")
        
        result = await memory_service.consolidate_session_memory(user_id, session_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "session_id": session_id,
            "result": result
        }
        
    except Exception as e:
        _logger.error(f"Error consolidando memoria: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/memory/profile/{user_id}")
async def get_user_profile_endpoint(user_id: str):
    """
    Obtiene el perfil de usuario con contexto persistente.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Perfil del usuario
    """
    try:
        profile = await memory_service.get_user_profile(user_id)
        return profile
        
    except Exception as e:
        _logger.error(f"Error obteniendo perfil de usuario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/memory/context/{user_id}")
async def get_user_context_endpoint(user_id: str, session_id: str = None, query: str = ""):
    """
    Obtiene contexto enriquecido para un usuario.
    
    Args:
        user_id: ID del usuario
        session_id: ID de la sesión (opcional)
        query: Consulta para búsqueda semántica (opcional)
    
    Returns:
        Contexto enriquecido
    """
    try:
        if not session_id:
            session_id = f"context_session_{int(datetime.now().timestamp())}"
        
        if not query:
            query = "Contexto general del usuario"
        
        enhanced_context = await memory_service.enrich_context(
            user_id=user_id,
            session_id=session_id,
            current_query=query
        )
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "enhanced_context": enhanced_context
        }
        
    except Exception as e:
        _logger.error(f"Error obteniendo contexto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

