"""
Orquestador principal de CorpChat - Agente ADK root.

Este agente coordina las consultas del usuario y delega a especialistas según necesidad.
"""

import logging
import sys
import os
from pathlib import Path

# Agregar shared al path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from google.adk.agents import LlmAgent
from google.adk.tools import google_search
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
- Determina qué especialista puede responder mejor la pregunta.
- Delega al especialista apropiado cuando sea necesario.
- Si la consulta es general o no requiere conocimiento especializado, responde directamente.
- Agrega contexto y valor a las respuestas de los especialistas.
- Mantén un tono profesional, claro y conciso.
- Siempre responde en español.

**Especialistas disponibles:**

- **Especialista de Conocimiento Empresarial**: Para consultas sobre la empresa.
- **Especialista de Estado Técnico**: Para consultas sobre sistemas y monitoreo.
- **Especialista de Productos**: Para información comercial y cotizaciones.

**Herramientas disponibles:**

- **Google Search**: Para información actualizada de internet cuando sea necesario.
- **Docs Tool**: Para leer documentos corporativos.
- **Sheets Tool**: Para consultar catálogos y tablas de datos.

**Directrices:**

1. Si no estás seguro de algo, admítelo y ofrece alternativas.
2. Cita las fuentes cuando uses información de documentos o bases de conocimiento.
3. Sé proactivo: sugiere información relacionada que pueda ser útil.
4. Mantén las respuestas concisas pero completas.
5. Si detectas que una consulta requiere múltiples especialistas, coordina las respuestas.
"""


def create_orchestrator_agent():
    """
    Crea y retorna el agente orquestador principal.
    
    Returns:
        LlmAgent configurado como orquestador
    """
    _logger.info("Creando orquestador ADK...")
    
    # Por ahora, crear orquestador sin sub_agents
    # Los sub_agents se agregarán cuando estén implementados
    
    orchestrator = LlmAgent(
        name="CorpChat",
        model=MODEL,
        instruction=ORCHESTRATOR_INSTRUCTION,
        description="Asistente corporativo que coordina consultas empresariales",
        tools=[google_search],
        # thinking_config se configurará cuando esté disponible en ADK 1.8.0
        # thinking_config={"enabled": True, "budget_tokens": 1000}
    )
    
    _logger.info(f"Orquestador creado con modelo {MODEL}")
    return orchestrator


# Crear instancia global del orquestador
root_agent = create_orchestrator_agent()


if __name__ == "__main__":
    _logger.info("Orquestador CorpChat inicializado")
    _logger.info(f"Modelo: {MODEL}")
    _logger.info(f"Proyecto: {PROJECT_ID}")
    _logger.info(f"Región: {LOCATION}")

