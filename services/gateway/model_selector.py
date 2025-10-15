"""
Model Selector para CorpChat - Modelos REALES de Gemini
"""

from typing import Dict, Optional
from enum import Enum


class ModelCapability(Enum):
    """Capacidades específicas de los modelos."""
    GENERAL = "general"
    THINKING = "thinking"
    CODING = "coding"
    IMAGE_GENERATION = "image_generation"
    ANALYSIS = "analysis"
    FAST = "fast"


class ModelConfig:
    """Configuración de un modelo real de Gemini."""
    def __init__(
        self,
        gemini_model: str,
        display_name: str,
        description: str,
        capability: ModelCapability,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        cost_per_1k_tokens: float = 0.075,
        supports_thinking: bool = False,
        supports_images: bool = False,
        supports_code: bool = False
    ):
        self.gemini_model = gemini_model
        self.display_name = display_name
        self.description = description
        self.capability = capability
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.supports_thinking = supports_thinking
        self.supports_images = supports_images
        self.supports_code = supports_code


# Modelos REALES de Gemini disponibles en Vertex AI
AVAILABLE_MODELS = {
    # Gemini 2.5 Flash - Modelo rápido y eficiente
    "gemini-2.5-flash": ModelConfig(
        gemini_model="gemini-2.5-flash-001",
        display_name="Gemini 2.5 Flash",
        description="Modelo rápido y eficiente para conversaciones generales",
        capability=ModelCapability.FAST,
        temperature=0.7,
        max_tokens=8192,
        cost_per_1k_tokens=0.075,
        supports_thinking=False,
        supports_images=False,
        supports_code=True
    ),
    
    # Gemini 2.5 Flash Thinking - Con capacidad de razonamiento
    "gemini-2.5-flash-thinking": ModelConfig(
        gemini_model="gemini-2.5-flash-001",
        display_name="Gemini 2.5 Flash (Thinking)",
        description="Modelo rápido con capacidad de razonamiento profundo",
        capability=ModelCapability.THINKING,
        temperature=0.7,
        max_tokens=8192,
        cost_per_1k_tokens=0.075,
        supports_thinking=True,
        supports_images=False,
        supports_code=True
    ),
    
    # Gemini 2.0 Flash - Modelo general equilibrado
    "gemini-2.0-flash": ModelConfig(
        gemini_model="gemini-2.0-flash-exp",
        display_name="Gemini 2.0 Flash",
        description="Modelo equilibrado para tareas generales y análisis",
        capability=ModelCapability.GENERAL,
        temperature=0.7,
        max_tokens=8192,
        cost_per_1k_tokens=0.075,
        supports_thinking=True,
        supports_images=True,
        supports_code=True
    ),
    
    # Gemini 1.5 Pro - Modelo avanzado para análisis complejos
    "gemini-1.5-pro": ModelConfig(
        gemini_model="gemini-1.5-pro-001",
        display_name="Gemini 1.5 Pro",
        description="Modelo avanzado para análisis complejos y razonamiento profundo",
        capability=ModelCapability.ANALYSIS,
        temperature=0.1,
        max_tokens=8192,
        cost_per_1k_tokens=0.00125,  # Más caro
        supports_thinking=True,
        supports_images=True,
        supports_code=True
    ),
    
    # Gemini 1.5 Flash - Modelo rápido para desarrollo
    "gemini-1.5-flash": ModelConfig(
        gemini_model="gemini-1.5-flash-001",
        display_name="Gemini 1.5 Flash",
        description="Modelo rápido optimizado para desarrollo y codificación",
        capability=ModelCapability.CODING,
        temperature=0.3,
        max_tokens=8192,
        cost_per_1k_tokens=0.075,
        supports_thinking=False,
        supports_images=False,
        supports_code=True
    ),
    
    # Gemini 1.5 Pro con imágenes - Para generación de contenido visual
    "gemini-1.5-pro-vision": ModelConfig(
        gemini_model="gemini-1.5-pro-001",
        display_name="Gemini 1.5 Pro (Vision)",
        description="Modelo avanzado con capacidades de análisis de imágenes y generación visual",
        capability=ModelCapability.IMAGE_GENERATION,
        temperature=0.7,
        max_tokens=8192,
        cost_per_1k_tokens=0.00125,
        supports_thinking=True,
        supports_images=True,
        supports_code=False
    )
}


def get_model_config(model_name: str) -> ModelConfig:
    """
    Obtiene la configuración de un modelo real de Gemini.
    
    Args:
        model_name: Nombre del modelo Gemini
        
    Returns:
        Configuración del modelo o modelo por defecto
    """
    return AVAILABLE_MODELS.get(model_name, AVAILABLE_MODELS["gemini-2.5-flash"])


def get_available_models() -> Dict[str, Dict]:
    """
    Retorna la lista de modelos REALES de Gemini disponibles para Open WebUI.
    
    Returns:
        Diccionario con información de modelos Gemini para Open WebUI
    """
    models = {}
    
    for gemini_name, config in AVAILABLE_MODELS.items():
        models[gemini_name] = {
            "id": gemini_name,
            "object": "model",
            "created": 1677610602,  # Timestamp fijo
            "owned_by": "google",
            "permission": [],
            "root": gemini_name,
            "parent": None,
            "display_name": config.display_name,
            "description": config.description,
            "capability": config.capability.value,
            "gemini_model": config.gemini_model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "cost_per_1k_tokens": config.cost_per_1k_tokens,
            "supports_thinking": config.supports_thinking,
            "supports_images": config.supports_images,
            "supports_code": config.supports_code
        }
    
    return models


def apply_model_config(model_config: ModelConfig, request_data: Dict) -> Dict:
    """
    Aplica la configuración del modelo Gemini al request.
    
    Args:
        model_config: Configuración del modelo Gemini
        request_data: Datos del request original
        
    Returns:
        Request modificado con configuración del modelo
    """
    # Crear copia del request
    modified_request = request_data.copy()
    
    # Aplicar configuración del modelo
    modified_request["temperature"] = model_config.temperature
    modified_request["max_tokens"] = min(
        model_config.max_tokens,
        request_data.get("max_tokens", 8192)
    )
    
    # Agregar metadata del modelo
    modified_request["gemini_model"] = model_config.gemini_model
    modified_request["capability"] = model_config.capability.value
    modified_request["supports_thinking"] = model_config.supports_thinking
    modified_request["supports_images"] = model_config.supports_images
    modified_request["supports_code"] = model_config.supports_code
    
    return modified_request


def get_capability_prompt(model_config: ModelConfig, user_message: str) -> str:
    """
    Genera prompt adicional basado en las capacidades del modelo Gemini.
    
    Args:
        model_config: Configuración del modelo Gemini
        user_message: Mensaje del usuario
        
    Returns:
        Prompt modificado con instrucciones específicas de capacidad
    """
    capability_instructions = {
        ModelCapability.FAST: "",  # Sin modificaciones para respuestas rápidas
        
        ModelCapability.THINKING: (
            "\n\n[INSTRUCCIÓN]: Usa tu capacidad de razonamiento para analizar esta consulta. "
            "Piensa paso a paso y proporciona una respuesta bien fundamentada."
        ),
        
        ModelCapability.CODING: (
            "\n\n[INSTRUCCIÓN]: Eres un experto en programación. Si la consulta involucra código, "
            "proporciona ejemplos prácticos y mejores prácticas. Si no es sobre programación, "
            "responde normalmente."
        ),
        
        ModelCapability.ANALYSIS: (
            "\n\n[INSTRUCCIÓN]: Realiza un análisis profundo y detallado. Considera múltiples "
            "perspectivas, proporciona evidencia y ejemplos concretos cuando sea apropiado."
        ),
        
        ModelCapability.IMAGE_GENERATION: (
            "\n\n[INSTRUCCIÓN]: Si la consulta involucra imágenes, análisis visual o generación "
            "de contenido visual, proporciona una respuesta detallada. Si no, responde normalmente."
        ),
        
        ModelCapability.GENERAL: ""  # Sin modificaciones para uso general
    }
    
    instruction = capability_instructions.get(model_config.capability, "")
    return user_message + instruction


# Endpoint para listar modelos (compatible con OpenAI)
def get_models_endpoint():
    """
    Endpoint para listar modelos REALES de Gemini disponibles.
    Compatible con OpenAI API format.
    """
    models = get_available_models()
    
    return {
        "object": "list",
        "data": list(models.values())
    }
