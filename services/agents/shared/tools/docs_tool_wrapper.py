"""
ADK Tool wrapper para Docs Tool HTTP API.

Permite a los agentes leer documentos corporativos desde GCS o Google Drive
a través del servicio corpchat-docs-tool.
"""

import logging
import httpx
from typing import Optional

_logger = logging.getLogger(__name__)

# URL del servicio Docs Tool (se configurará via env var en producción)
DOCS_TOOL_URL = "http://localhost:8081"  # Placeholder para desarrollo


async def read_corporate_document(
    doc_path: str,
    doc_type: str = "gcs"
) -> str:
    """
    Lee un documento corporativo desde GCS o Google Drive.
    
    Args:
        doc_path: Ruta del documento
            - Para GCS: "gs://bucket/path/to/doc.pdf"
            - Para GDrive: ID del documento
        doc_type: Tipo de documento ("gcs" o "gdrive")
    
    Returns:
        Contenido del documento o mensaje de error
    
    Example:
        >>> content = await read_corporate_document("gs://corp-docs/policies/vacation.pdf")
        >>> print(content)
        "Política de Vacaciones\n\nLas vacaciones anuales..."
    """
    try:
        _logger.info(f"📄 Leyendo documento: {doc_path} ({doc_type})")
        
        # En MVP, retornar placeholder
        # En producción, hacer HTTP call a corpchat-docs-tool
        
        # TODO: Implementar llamada HTTP real cuando el servicio esté deployed
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{DOCS_TOOL_URL}/read",
        #         json={"path": doc_path, "type": doc_type}
        #     )
        #     return response.json()["content"]
        
        _logger.warning("⚠️ Docs Tool no implementado aún, retornando placeholder")
        return f"[Placeholder] Contenido del documento: {doc_path}\n\nEste es un placeholder. El servicio Docs Tool se implementará en la siguiente iteración."
    
    except Exception as e:
        _logger.error(f"❌ Error leyendo documento: {e}", exc_info=True)
        return f"Error al leer el documento: {str(e)}"


async def list_corporate_documents(
    folder_path: str,
    doc_type: str = "gcs"
) -> str:
    """
    Lista documentos disponibles en un folder corporativo.
    
    Args:
        folder_path: Ruta del folder
        doc_type: Tipo de storage ("gcs" o "gdrive")
    
    Returns:
        Lista de documentos disponibles
    """
    try:
        _logger.info(f"📂 Listando documentos en: {folder_path}")
        
        # Placeholder para MVP
        return f"[Placeholder] Documentos en {folder_path}:\n- doc1.pdf\n- doc2.docx\n\nDocs Tool se implementará pronto."
    
    except Exception as e:
        _logger.error(f"❌ Error listando documentos: {e}", exc_info=True)
        return f"Error al listar documentos: {str(e)}"


__all__ = ["read_corporate_document", "list_corporate_documents"]

