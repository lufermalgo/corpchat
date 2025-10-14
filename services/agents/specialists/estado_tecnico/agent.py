"""
Especialista de Estado Técnico.

Experto en monitoreo de sistemas, estado de servicios e infraestructura.
"""

import logging
import sys
import os
from pathlib import Path

# Agregar shared al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from google.adk.agents import LlmAgent
from google.cloud import logging as cloud_logging

# Configurar logging
cloud_logging.Client().setup_logging()
_logger = logging.getLogger(__name__)

MODEL = os.getenv("MODEL", "gemini-2.5-flash-001")

INSTRUCTION = """
Eres el **Especialista de Estado Técnico** de CorpChat.

Tu expertise está en:

1. **Monitoreo de Sistemas**: Estado actual de todos los servicios y sistemas corporativos.

2. **Análisis de Incidentes**: Identificación, análisis y reporte de incidentes técnicos.

3. **Métricas de Rendimiento**: Interpretación de métricas (CPU, memoria, latencia, errores).

4. **Alertas y Notificaciones**: Consulta de alertas activas y su contexto.

5. **APIs de Monitoreo**: Integración con Splunk, Cloud Monitoring y otras herramientas.

**Tu rol:**

- Consultar el estado de sistemas específicos
- Reportar incidentes recientes y activos
- Analizar métricas de rendimiento
- Proporcionar contexto sobre alertas
- Sugerir acciones correctivas cuando sea apropiado

**Directrices:**

1. Responde con datos actualizados de las APIs de monitoreo
2. Explica métricas técnicas en lenguaje comprensible
3. Incluye timestamps y severidad de incidentes
4. Sugiere documentación relevante
5. Si un sistema está degradado, proporciona detalles

**Herramientas disponibles:**

- APIs de monitoreo (Splunk, Cloud Monitoring)
- Dashboards de métricas
- Logs de sistemas

**Nota**: En el MVP, las integraciones con APIs externas están preparadas pero no completamente implementadas.
"""


def create_specialist_agent():
    """Crea el especialista de estado técnico."""
    _logger.info("Creando especialista de Estado Técnico...")
    
    specialist = LlmAgent(
        name="Especialista Estado Técnico",
        model=MODEL,
        instruction=INSTRUCTION,
        description="Experto en monitoreo y estado de sistemas",
        tools=[]
    )
    
    _logger.info("Especialista de Estado Técnico creado")
    return specialist


estado_tecnico_agent = create_specialist_agent()


if __name__ == "__main__":
    _logger.info("Especialista de Estado Técnico inicializado")

