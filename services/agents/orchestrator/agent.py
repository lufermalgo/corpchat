"""
Orquestador principal de CorpChat usando ADK (Agent Development Kit).

Este agente coordina las consultas del usuario y delega a especialistas según necesidad.
Usa Google ADK para multi-agent orchestration.
"""

import logging
import sys
import os
from pathlib import Path

# Agregar shared al path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from google.adk.agents import LlmAgent
from google.cloud import logging as cloud_logging

# Configurar logging
try:
    cloud_logging.Client().setup_logging()
except Exception as e:
    logging.warning(f"No se pudo configurar Cloud Logging: {e}")

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
- Determina qué especialista puede responder mejor la pregunta.
- Delega al especialista apropiado cuando sea necesario usando transfer().
- Si la consulta es general o no requiere conocimiento especializado, responde directamente.
- Agrega contexto y valor a las respuestas de los especialistas.
- Mantén un tono profesional, claro y conciso.
- Siempre responde en español.

**Especialistas disponibles:**

- **Especialista de Conocimiento Empresarial**: Para consultas sobre la empresa.
- **Especialista de Estado Técnico**: Para consultas sobre sistemas y monitoreo.
- **Especialista de Productos**: Para información comercial y cotizaciones.

**Directrices:**

1. Si no estás seguro de algo, admítelo y ofrece alternativas.
2. Cita las fuentes cuando uses información de documentos o bases de conocimiento.
3. Sé proactivo: sugiere información relacionada que pueda ser útil.
4. Mantén las respuestas concisas pero completas.
5. Si detectas que una consulta requiere múltiples especialistas, coordina las respuestas.
"""


def create_orchestrator_agent():
    """
    Crea y retorna el agente orquestador principal usando ADK.
    
    Returns:
        LlmAgent configurado como orquestador
    """
    _logger.info("Creando orquestador ADK...")
    _logger.info(f"Modelo: {MODEL}, Proyecto: {PROJECT_ID}, Región: {LOCATION}")
    
    try:
        # Crear orquestador usando ADK
        # Nota: Por ahora sin sub_agents, se agregarán progresivamente
        orchestrator = LlmAgent(
            name="CorpChat",
            model=MODEL,
            instruction=ORCHESTRATOR_INSTRUCTION,
            description="Asistente corporativo que coordina consultas empresariales",
            # sub_agents se agregarán cuando estén implementados los especialistas
            # tools se agregarán progresivamente (google_search, custom tools, etc.)
        )
        
        _logger.info(f"✅ Orquestador ADK creado exitosamente")
        return orchestrator
        
    except Exception as e:
        _logger.error(f"❌ Error creando orquestador ADK: {e}", exc_info=True)
        raise


# Crear instancia global del orquestador
try:
    root_agent = create_orchestrator_agent()
    _logger.info("🚀 Orquestador CorpChat listo")
except Exception as e:
    _logger.error(f"💥 Error fatal inicializando orquestador: {e}")
    # No hacer raise aquí para que el módulo pueda importarse
    # El error se manejará en main.py
    root_agent = None


if __name__ == "__main__":
    if root_agent:
        _logger.info("✅ Orquestador CorpChat inicializado correctamente")
        _logger.info(f"📊 Modelo: {MODEL}")
        _logger.info(f"📍 Proyecto: {PROJECT_ID}")
        _logger.info(f"🌍 Región: {LOCATION}")
    else:
        _logger.error("❌ El orquestador no se inicializó correctamente")
