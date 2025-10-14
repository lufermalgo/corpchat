"""
Utilidades compartidas para agentes ADK.
"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime

_logger = logging.getLogger(__name__)


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Obtiene una variable de entorno de forma segura.
    
    Args:
        key: Nombre de la variable
        default: Valor por defecto
        required: Si es obligatoria, lanza excepción si no existe
    
    Returns:
        Valor de la variable o default
    
    Raises:
        ValueError: Si es required y no existe
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Variable de entorno requerida no encontrada: {key}")
    
    return value


def extract_user_from_iap_header(header_value: Optional[str]) -> str:
    """
    Extrae el email del usuario desde el header de IAP.
    
    Args:
        header_value: Valor del header X-Goog-Authenticated-User-Email
    
    Returns:
        Email del usuario o "anonymous"
    """
    if not header_value:
        return "anonymous"
    
    # Formato: accounts.google.com:user@domain.com
    if ":" in header_value:
        return header_value.split(":")[-1]
    
    return header_value


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "gemini-2.5-flash-001"
) -> float:
    """
    Estima el costo de una operación con Gemini.
    
    Precios aproximados (actualizar según pricing real):
    - Gemini 2.5 Flash:
      * Input: $0.075 / 1M tokens
      * Output: $0.30 / 1M tokens
    
    Args:
        prompt_tokens: Tokens del prompt
        completion_tokens: Tokens de la respuesta
        model: Nombre del modelo
    
    Returns:
        Costo estimado en USD
    """
    # Precios por 1M tokens
    pricing = {
        "gemini-2.5-flash-001": {
            "input": 0.075,
            "output": 0.30
        },
        "gemini-1.5-pro": {
            "input": 1.25,
            "output": 5.00
        },
        "gemini-1.5-flash": {
            "input": 0.075,
            "output": 0.30
        }
    }
    
    model_pricing = pricing.get(model, pricing["gemini-2.5-flash-001"])
    
    input_cost = (prompt_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * model_pricing["output"]
    
    return input_cost + output_cost


def log_agent_invocation(
    agent_name: str,
    user_id: str,
    chat_id: str,
    tokens: int,
    latency_ms: float,
    cost_usd: float,
    success: bool = True,
    error: Optional[str] = None
) -> None:
    """
    Log estructurado de invocación de agente.
    
    Args:
        agent_name: Nombre del agente
        user_id: ID del usuario
        chat_id: ID del chat
        tokens: Tokens consumidos
        latency_ms: Latencia en milisegundos
        cost_usd: Costo estimado en USD
        success: Si la invocación fue exitosa
        error: Mensaje de error si aplica
    """
    _logger.info(
        f"Agent invocation: {agent_name}",
        extra={
            "agent_name": agent_name,
            "user_id": user_id,
            "chat_id": chat_id,
            "tokens": tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "labels": {
                "service": "agents",
                "team": "corpchat",
                "agent": agent_name
            }
        }
    )


def format_chat_history_for_prompt(messages: list) -> str:
    """
    Formatea el historial de chat para incluir en un prompt.
    
    Args:
        messages: Lista de mensajes del chat
    
    Returns:
        Historial formateado como texto
    """
    if not messages:
        return "No hay historial previo."
    
    formatted = []
    for msg in messages[-10:]:  # Últimos 10 mensajes
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        timestamp = msg.get('timestamp', datetime.now())
        
        formatted.append(f"{role.upper()} [{timestamp}]:\n{content}\n")
    
    return "\n".join(formatted)


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Trunca un texto a una longitud máxima.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a agregar si se trunca
    
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo para GCS.
    
    Args:
        filename: Nombre original
    
    Returns:
        Nombre sanitizado
    """
    import re
    # Remover caracteres no permitidos
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Limitar longitud
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized


def parse_mime_type(mime_type: str) -> Dict[str, str]:
    """
    Parsea un MIME type.
    
    Args:
        mime_type: MIME type (ej: "application/pdf")
    
    Returns:
        Dict con 'type' y 'subtype'
    """
    parts = mime_type.split('/')
    return {
        'type': parts[0] if len(parts) > 0 else 'unknown',
        'subtype': parts[1] if len(parts) > 1 else 'unknown'
    }


def is_supported_document(mime_type: str) -> bool:
    """
    Verifica si un MIME type es un documento soportado.
    
    Args:
        mime_type: MIME type
    
    Returns:
        True si es soportado
    """
    supported = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # XLSX
        'application/msword',  # DOC
        'application/vnd.ms-excel',  # XLS
        'text/plain',
        'text/csv',
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/webp'
    ]
    
    return mime_type in supported


def format_bytes(size_bytes: int) -> str:
    """
    Formatea un tamaño en bytes a formato legible.
    
    Args:
        size_bytes: Tamaño en bytes
    
    Returns:
        Tamaño formateado (ej: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


class RateLimiter:
    """Rate limiter simple basado en memoria (para MVP)."""
    
    def __init__(self):
        """Inicializa el rate limiter."""
        self._counters: Dict[str, Dict[str, Any]] = {}
    
    def check_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> bool:
        """
        Verifica si se excedió el límite.
        
        Args:
            key: Clave única (ej: user_id)
            limit: Límite de operaciones
            window_seconds: Ventana de tiempo en segundos
        
        Returns:
            True si está dentro del límite
        """
        now = datetime.now()
        
        if key not in self._counters:
            self._counters[key] = {
                'count': 1,
                'window_start': now
            }
            return True
        
        counter = self._counters[key]
        elapsed = (now - counter['window_start']).total_seconds()
        
        if elapsed > window_seconds:
            # Reset window
            counter['count'] = 1
            counter['window_start'] = now
            return True
        
        if counter['count'] >= limit:
            return False
        
        counter['count'] += 1
        return True


# Instancia global de rate limiter para importar
rate_limiter = RateLimiter()

