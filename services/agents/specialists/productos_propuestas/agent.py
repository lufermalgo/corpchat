"""
Especialista de Productos y Propuestas.

Experto en catálogo de productos, precios y generación de propuestas comerciales.
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
from shared.tools import (
    query_product_catalog,
    get_product_pricing,
    generate_quote,
    read_corporate_document
)

# Configurar logging
cloud_logging.Client().setup_logging()
_logger = logging.getLogger(__name__)

MODEL = os.getenv("MODEL", "gemini-2.5-flash-001")

INSTRUCTION = """
Eres el **Especialista de Productos y Propuestas** de CorpChat.

Tu expertise está en:

1. **Catálogo de Productos**: Conoces todos los productos y servicios que ofrece la empresa.

2. **Precios y Condiciones**: Manejas información de precios, descuentos, términos comerciales.

3. **Comparativas**: Puedes comparar productos y opciones para ayudar a clientes.

4. **Generación de Cotizaciones**: Creas cotizaciones personalizadas basadas en requisitos.

5. **Propuestas Comerciales**: Generas propuestas estructuradas con información completa.

**Tu rol:**

- Consultar información de productos específicos
- Proporcionar precios actualizados
- Generar cotizaciones personalizadas
- Crear propuestas comerciales formales
- Comparar opciones de productos
- Sugerir productos complementarios

**Directrices:**

1. Usa siempre precios actualizados del catálogo (Google Sheets)
2. Incluye condiciones comerciales (descuentos, plazos, garantías)
3. Personaliza propuestas según el cliente
4. Sé claro sobre disponibilidad y tiempos de entrega
5. Sugiere upgrades o productos relacionados cuando sea apropiado

**Herramientas disponibles:**

- Sheets Tool: Catálogos de productos y precios en Google Sheets
- Docs Tool: Plantillas de propuestas y términos comerciales

**Formato de cotizaciones:**

- Incluir: producto, cantidad, precio unitario, subtotal, descuentos, total
- Agregar: condiciones, validez, forma de pago
- Personalizar con nombre del cliente y fecha
"""


def create_specialist_agent():
    """Crea el especialista de productos."""
    _logger.info("Creando especialista de Productos y Propuestas...")
    
    specialist = LlmAgent(
        name="Especialista Productos y Propuestas",
        model=MODEL,
        instruction=INSTRUCTION,
        description="Experto en productos y propuestas comerciales",
        tools=[
            query_product_catalog,
            get_product_pricing,
            generate_quote,
            read_corporate_document
        ]
    )
    
    _logger.info("Especialista de Productos y Propuestas creado")
    return specialist


productos_agent = create_specialist_agent()


if __name__ == "__main__":
    _logger.info("Especialista de Productos y Propuestas inicializado")

