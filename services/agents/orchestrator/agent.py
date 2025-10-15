"""
Orquestador principal de CorpChat - Versión MVP sin ADK.

Este agente coordina las consultas del usuario usando directamente Vertex AI Gemini.
NOTA: La integración completa de ADK se realizará en una fase posterior.
"""

import logging
import sys
import os
from pathlib import Path

# Agregar shared al path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
from google.cloud import logging as cloud_logging

# Configurar logging
cloud_logging.Client().setup_logging()
_logger = logging.getLogger(__name__)

# Variables de entorno
PROJECT_ID = os.getenv("VERTEX_PROJECT", "genai-385616")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
MODEL = os.getenv("MODEL", "gemini-2.5-flash-001")

# Instrucción del orquestador
ORCHESTRATOR_INSTRUCTION = """
Eres CorpChat, el asistente corporativo inteligente. Tu misión es ayudar a los empleados 
de la empresa con consultas sobre tres áreas principales:

1. **Conocimiento Empresarial**: Políticas, procesos, historia, cultura organizacional, 
   estructura de equipos, procedimientos internos.

2. **Estado Técnico**: Monitoreo de sistemas, estado de servicios, incidentes, 
   métricas de rendimiento, alertas activas.

3. **Productos y Propuestas**: Información de productos, precios, generación de cotizaciones,
   creación de propuestas comerciales, comparativas.

**Tu rol como orquestador:**

- Analiza cuidadosamente la consulta del usuario para entender su intención.
- Mantén un tono profesional, claro y conciso.
- Siempre responde en español.
- Si no estás seguro de algo, admítelo y ofrece alternativas.
- Sé proactivo: sugiere información relacionada que pueda ser útil.
- Mantén las respuestas concisas pero completas.
"""


class OrchestratorAgent:
    """Agente orquestador usando Vertex AI Gemini directamente (MVP)."""
    
    def __init__(self):
        """Inicializa el orquestador."""
        _logger.info("Inicializando orquestador CorpChat...")
        _logger.info(f"Proyecto: {PROJECT_ID}, Región: {LOCATION}, Modelo: {MODEL}")
        
        # Inicializar Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Crear modelo generativo
        self.model = GenerativeModel(
            model_name=MODEL,
            system_instruction=ORCHESTRATOR_INSTRUCTION
        )
        
        # Chat sessions cache (por usuario)
        self._sessions = {}
        
        _logger.info("Orquestador inicializado exitosamente")
    
    def get_session(self, user_id: str) -> ChatSession:
        """
        Obtiene o crea una sesión de chat para un usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            ChatSession para el usuario
        """
        if user_id not in self._sessions:
            self._sessions[user_id] = self.model.start_chat()
            _logger.info(f"Nueva sesión creada para usuario {user_id}")
        
        return self._sessions[user_id]
    
    def chat(self, message: str, user_id: str = "default") -> str:
        """
        Procesa un mensaje del usuario y retorna la respuesta.
        
        Args:
            message: Mensaje del usuario
            user_id: ID del usuario (opcional)
        
        Returns:
            Respuesta generada
        """
        try:
            session = self.get_session(user_id)
            response = session.send_message(message)
            return response.text
        except Exception as e:
            _logger.error(f"Error procesando mensaje: {e}", exc_info=True)
            return f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}"
    
    def clear_session(self, user_id: str):
        """
        Limpia la sesión de un usuario.
        
        Args:
            user_id: ID del usuario
        """
        if user_id in self._sessions:
            del self._sessions[user_id]
            _logger.info(f"Sesión limpiada para usuario {user_id}")


# Crear instancia global del orquestador
root_agent = OrchestratorAgent()


if __name__ == "__main__":
    _logger.info("Orquestador CorpChat listo")
    _logger.info(f"Modelo: {MODEL}")
    _logger.info(f"Proyecto: {PROJECT_ID}")
    _logger.info(f"Región: {LOCATION}")
