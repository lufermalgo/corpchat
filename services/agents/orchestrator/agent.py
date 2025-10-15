"""
Orquestador principal de CorpChat usando ADK (Agent Development Kit).

Este agente coordina las consultas del usuario y delega a especialistas según necesidad.
Usa Google ADK para multi-agent orchestration.
"""

import logging
import sys
import os
from pathlib import Path

# Agregar shared al path si es necesario (desarrollo local)
shared_path = Path(__file__).parent.parent / "shared"
if shared_path.exists() and str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from google.adk.agents import LlmAgent

# Importar especialistas
from specialists.conocimiento_empresa.agent import conocimiento_agent
from specialists.estado_tecnico.agent import estado_tecnico_agent
from specialists.productos_propuestas.agent import productos_agent

_logger = logging.getLogger(__name__)

# Variables de entorno
PROJECT_ID = os.getenv("VERTEX_PROJECT", "genai-385616")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
MODEL = os.getenv("MODEL", "gemini-2.0-flash")

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
    
    IMPORTANTE: Se llama bajo demanda, no en el módulo global,
    para evitar timeouts en la inicialización del contenedor.
    
    Returns:
        LlmAgent configurado como orquestador
    """
    _logger.info(f"🔧 Creando orquestador ADK...")
    _logger.info(f"📊 Modelo: {MODEL}, Proyecto: {PROJECT_ID}, Región: {LOCATION}")
    
    try:
        # Crear orquestador usando ADK con sub-agents
        orchestrator = LlmAgent(
            name="CorpChat",
            model=MODEL,
            instruction=ORCHESTRATOR_INSTRUCTION,
            description="Asistente corporativo que coordina consultas empresariales",
            sub_agents=[
                conocimiento_agent,
                estado_tecnico_agent,
                productos_agent
            ]
            # tools se agregarán progresivamente (google_search, custom tools, etc.)
        )
        
        _logger.info(f"✅ Orquestador ADK creado exitosamente")
        return orchestrator
        
    except Exception as e:
        _logger.error(f"❌ Error creando orquestador ADK: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Test local
    try:
        agent = create_orchestrator_agent()
        _logger.info("✅ Test: Orquestador creado correctamente")
    except Exception as e:
        _logger.error(f"❌ Test falló: {e}")
