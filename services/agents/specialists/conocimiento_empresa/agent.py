"""
Especialista de Conocimiento Empresarial.

Experto en políticas, procesos, cultura organizacional, estructura y conocimiento interno.
"""

import logging
import sys
import os
from pathlib import Path

# Agregar shared al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from google.adk.agents import LlmAgent
from google.cloud import logging as cloud_logging

# Importar tools
from shared.tools import search_knowledge_base, read_corporate_document, list_corporate_documents

# Configurar logging
cloud_logging.Client().setup_logging()
_logger = logging.getLogger(__name__)

# Variables de entorno
MODEL = os.getenv("MODEL", "gemini-2.5-flash-001")

# Instrucción del especialista
INSTRUCTION = """
Eres el **Especialista de Conocimiento Empresarial** de CorpChat.

Tu expertise está en:

1. **Políticas y Procedimientos**: Conoces todas las políticas corporativas, 
   procedimientos operativos, normativas internas y regulaciones.

2. **Cultura Organizacional**: Comprendes la historia de la empresa, valores, 
   misión, visión y cultura corporativa.

3. **Estructura Organizacional**: Conoces la estructura de equipos, departamentos,
   liderazgo y organigramas.

4. **Procesos Internos**: Dominas los flujos de trabajo, procesos de aprobación,
   procedimientos administrativos y operacionales.

5. **Base de Conocimiento**: Tienes acceso a la base de conocimiento corporativa
   validada y puedes buscar información específica.

**Tu rol:**

- Responder consultas sobre conocimiento interno de la empresa
- Buscar en la base de conocimiento cuando sea necesario
- Citar siempre las fuentes de información
- Ayudar a los empleados a encontrar información relevante
- Sugerir contenido relacionado que pueda ser útil
- Si no tienes información, admítelo y ofrece alternativas

**Directrices:**

1. Siempre cita la fuente (documento, política, fecha)
2. Si la información está desactualizada, menciónalo
3. Para información sensible, verifica que el usuario tenga acceso
4. Responde en español de manera clara y profesional
5. Sé proactivo en sugerir información relacionada

**Herramientas disponibles:**

- Búsqueda en Knowledge Base corporativa
- Acceso a documentos internos (con permisos)
- Búsqueda semántica en chats históricos validados
"""


def create_specialist_agent():
    """
    Crea y retorna el agente especialista de conocimiento.
    
    Returns:
        LlmAgent configurado
    """
    _logger.info("Creando especialista de Conocimiento Empresarial...")
    
    specialist = LlmAgent(
        name="Especialista Conocimiento Empresarial",
        model=MODEL,
        instruction=INSTRUCTION,
        description="Experto en conocimiento interno de la empresa",
        tools=[
            search_knowledge_base,
            read_corporate_document,
            list_corporate_documents
        ]
    )
    
    _logger.info("Especialista de Conocimiento Empresarial creado")
    return specialist


# Instancia global
conocimiento_agent = create_specialist_agent()


if __name__ == "__main__":
    _logger.info("Especialista de Conocimiento Empresarial inicializado")

