"""
Model Selector para CorpChat - Mapeo de modelos OpenAI a Vertex AI Gemini
"""

from typing import Dict, Optional
from enum import Enum


class ThinkingMode(Enum):
    """Modos de pensamiento disponibles."""
    AUTO = "auto"
    INSTANT = "instant"
    THINKING_MINI = "thinking_mini"
    THINKING = "thinking"


class ModelConfig:
    """Configuración de un modelo."""
    def __init__(
        self,
        vertex_model: str,
        display_name: str,
        description: str,
        thinking_mode: ThinkingMode,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        cost_per_1k_tokens: float = 0.075
    ):
        self.vertex_model = vertex_model
        self.display_name = display_name
        self.description = description
        self.thinking_mode = thinking_mode
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cost_per_1k_tokens = cost_per_1k_tokens


# Configuración de modelos disponibles
AVAILABLE_MODELS = {
    # Modelos rápidos (Instant)
    "gpt-4o-mini": ModelConfig(
        vertex_model="gemini-2.5-flash-001",
        display_name="CorpChat Instant",
        description="Respuestas rápidas para consultas simples",
        thinking_mode=ThinkingMode.INSTANT,
        temperature=0.3,
        max_tokens=1024,
        cost_per_1k_tokens=0.075
    ),
    
    "gpt-4o": ModelConfig(
        vertex_model="gemini-2.5-flash-001",
        display_name="CorpChat Standard",
        description="Balance entre velocidad y calidad",
        thinking_mode=ThinkingMode.THINKING_MINI,
        temperature=0.7,
        max_tokens=2048,
        cost_per_1k_tokens=0.075
    ),
    
    # Modelos que piensan más (Thinking)
    "gpt-4": ModelConfig(
        vertex_model="gemini-2.5-flash-001",
        display_name="CorpChat Thinking",
        description="Piensa más tiempo para mejores respuestas",
        thinking_mode=ThinkingMode.THINKING,
        temperature=0.9,
        max_tokens=4096,
        cost_per_1k_tokens=0.075
    ),
    
    # Modelos especializados
    "gpt-4-turbo": ModelConfig(
        vertex_model="gemini-2.5-flash-001",
        display_name="CorpChat Turbo",
        description="Máxima velocidad con calidad",
        thinking_mode=ThinkingMode.AUTO,
        temperature=0.5,
        max_tokens=8192,
        cost_per_1k_tokens=0.075
    ),
    
    # Modelo para análisis complejos
    "gpt-4o-2024-07-18": ModelConfig(
        vertex_model="gemini-2.5-flash-001",
        display_name="CorpChat Analyst",
        description="Análisis profundo y razonamiento complejo",
        thinking_mode=ThinkingMode.THINKING,
        temperature=0.1,
        max_tokens=8192,
        cost_per_1k_tokens=0.075
    ),
    
    # Modelo por defecto
    "gpt-3.5-turbo": ModelConfig(
        vertex_model="gemini-2.5-flash-001",
        display_name="CorpChat Basic",
        description="Modelo básico para uso general",
        thinking_mode=ThinkingMode.INSTANT,
        temperature=0.7,
        max_tokens=1024,
        cost_per_1k_tokens=0.075
    )
}


def get_model_config(model_name: str) -> ModelConfig:
    """
    Obtiene la configuración de un modelo.
    
    Args:
        model_name: Nombre del modelo OpenAI
        
    Returns:
        Configuración del modelo o modelo por defecto
    """
    return AVAILABLE_MODELS.get(model_name, AVAILABLE_MODELS["gpt-3.5-turbo"])


def get_available_models() -> Dict[str, Dict]:
    """
    Retorna la lista de modelos disponibles para Open WebUI.
    
    Returns:
        Diccionario con información de modelos para Open WebUI
    """
    models = {}
    
    for openai_name, config in AVAILABLE_MODELS.items():
        models[openai_name] = {
            "id": openai_name,
            "object": "model",
            "created": 1677610602,  # Timestamp fijo
            "owned_by": "corpchat",
            "permission": [],
            "root": openai_name,
            "parent": None,
            "display_name": config.display_name,
            "description": config.description,
            "thinking_mode": config.thinking_mode.value,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "cost_per_1k_tokens": config.cost_per_1k_tokens
        }
    
    return models


def apply_thinking_mode(model_config: ModelConfig, request_data: Dict) -> Dict:
    """
    Aplica el modo de pensamiento a la configuración del request.
    
    Args:
        model_config: Configuración del modelo
        request_data: Datos del request original
        
    Returns:
        Request modificado con configuración de thinking mode
    """
    # Crear copia del request
    modified_request = request_data.copy()
    
    # Aplicar configuración del modelo
    modified_request["temperature"] = model_config.temperature
    modified_request["max_tokens"] = min(
        model_config.max_tokens,
        request_data.get("max_tokens", 2048)
    )
    
    # Agregar metadata de thinking mode
    modified_request["thinking_mode"] = model_config.thinking_mode.value
    
    return modified_request


def get_thinking_prompt(model_config: ModelConfig, user_message: str) -> str:
    """
    Genera prompt adicional basado en el modo de pensamiento.
    
    Args:
        model_config: Configuración del modelo
        user_message: Mensaje del usuario
        
    Returns:
        Prompt modificado con instrucciones de thinking
    """
    thinking_instructions = {
        ThinkingMode.INSTANT: "",
        
        ThinkingMode.THINKING_MINI: (
            "\n\n[INSTRUCCIÓN]: Piensa rápidamente pero de manera estructurada. "
            "Proporciona una respuesta directa y útil."
        ),
        
        ThinkingMode.THINKING: (
            "\n\n[INSTRUCCIÓN]: Piensa detenidamente sobre esta consulta. "
            "Considera múltiples perspectivas, analiza las implicaciones, "
            "y proporciona una respuesta completa y bien fundamentada. "
            "Si es relevante, incluye ejemplos o casos de uso."
        ),
        
        ThinkingMode.AUTO: (
            "\n\n[INSTRUCCIÓN]: Determina automáticamente el nivel de "
            "análisis necesario para esta consulta. Si es simple, responde "
            "directamente. Si es compleja, toma tiempo para analizarla a fondo."
        )
    }
    
    instruction = thinking_instructions.get(model_config.thinking_mode, "")
    return user_message + instruction


# Endpoint para listar modelos (compatible con OpenAI)
def get_models_endpoint():
    """
    Endpoint para listar modelos disponibles.
    Compatible con OpenAI API format.
    """
    models = get_available_models()
    
    return {
        "object": "list",
        "data": list(models.values())
    }
