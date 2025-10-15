"""
Router de Eventos GCS → Extractores.

Este módulo:
1. Recibe eventos de Pub/Sub cuando se crea un archivo en GCS
2. Determina el tipo de archivo (PDF, DOCX, XLSX, imagen)
3. Dispatch al extractor apropiado
4. Maneja errores y retries
"""

import logging
import mimetypes
from typing import Dict, Any, Optional
from pathlib import Path

_logger = logging.getLogger(__name__)

# Mapeo de MIME types a extractores
MIME_TO_EXTRACTOR = {
    # PDFs
    "application/pdf": "pdf",
    
    # Word documents
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
    
    # Excel/Spreadsheets
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-excel": "xls",
    
    # Images
    "image/png": "image",
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/gif": "image",
    "image/webp": "image",
    "image/bmp": "image",
    "image/tiff": "image",
    
    # Text
    "text/plain": "text",
    "text/csv": "csv"
}

# Extensiones de archivo a tipo
EXTENSION_TO_TYPE = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "doc",
    ".xlsx": "xlsx",
    ".xls": "xls",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
    ".txt": "text",
    ".csv": "csv"
}


class DocumentRouter:
    """
    Router que determina cómo procesar un documento.
    
    Basado en MIME type y extensión, selecciona el extractor apropiado.
    """
    
    def __init__(self):
        """Inicializa el router."""
        _logger.info("🚦 DocumentRouter inicializado")
    
    def determine_extractor(
        self,
        gcs_path: str,
        mime_type: Optional[str] = None
    ) -> str:
        """
        Determina qué extractor usar para un archivo.
        
        Args:
            gcs_path: Ruta del archivo en GCS
            mime_type: Tipo MIME (opcional)
        
        Returns:
            Nombre del extractor: "pdf", "docx", "xlsx", "image", "text"
        
        Raises:
            ValueError: Si el tipo de archivo no es soportado
        
        Example:
            >>> router = DocumentRouter()
            >>> extractor = router.determine_extractor("gs://bucket/doc.pdf")
            >>> print(extractor)
            "pdf"
        """
        # Opción 1: Usar MIME type si está disponible
        if mime_type and mime_type in MIME_TO_EXTRACTOR:
            extractor = MIME_TO_EXTRACTOR[mime_type]
            _logger.debug(f"🎯 Extractor determinado por MIME: {extractor} ({mime_type})")
            return extractor
        
        # Opción 2: Usar extensión de archivo
        file_path = Path(gcs_path)
        extension = file_path.suffix.lower()
        
        if extension in EXTENSION_TO_TYPE:
            extractor = EXTENSION_TO_TYPE[extension]
            _logger.debug(f"🎯 Extractor determinado por extensión: {extractor} ({extension})")
            return extractor
        
        # Si no se puede determinar, error
        raise ValueError(
            f"Tipo de archivo no soportado: {gcs_path} "
            f"(MIME: {mime_type}, Extension: {extension})"
        )
    
    def validate_file_size(self, size_bytes: int, max_size_mb: int = 100) -> bool:
        """
        Valida que el tamaño del archivo esté dentro de los límites.
        
        Args:
            size_bytes: Tamaño en bytes
            max_size_mb: Tamaño máximo permitido en MB
        
        Returns:
            True si es válido, False si excede el límite
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if size_bytes > max_size_bytes:
            _logger.warning(
                f"⚠️ Archivo excede tamaño máximo: "
                f"{size_bytes / 1024 / 1024:.2f} MB > {max_size_mb} MB"
            )
            return False
        
        return True
    
    def parse_gcs_notification(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parsea un evento de notificación de GCS.
        
        Cloud Storage Pub/Sub notification format:
        https://cloud.google.com/storage/docs/pubsub-notifications
        
        Args:
            event: Evento de Pub/Sub
        
        Returns:
            Diccionario con metadata parseada:
            {
                "bucket": "bucket-name",
                "name": "path/to/file.pdf",
                "gcs_path": "gs://bucket-name/path/to/file.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 12345,
                "event_type": "OBJECT_FINALIZE"
            }
        
        Raises:
            ValueError: Si el formato del evento es inválido
        """
        try:
            # Formato esperado de GCS notification
            # {
            #   "kind": "storage#object",
            #   "id": "...",
            #   "bucket": "bucket-name",
            #   "name": "path/to/file.pdf",
            #   "contentType": "application/pdf",
            #   "size": "12345",
            #   "eventType": "OBJECT_FINALIZE"
            # }
            
            bucket = event.get("bucket")
            name = event.get("name")
            
            if not bucket or not name:
                raise ValueError("Evento inválido: falta 'bucket' o 'name'")
            
            gcs_path = f"gs://{bucket}/{name}"
            mime_type = event.get("contentType")
            size_bytes = int(event.get("size", 0))
            event_type = event.get("eventType", "UNKNOWN")
            
            result = {
                "bucket": bucket,
                "name": name,
                "gcs_path": gcs_path,
                "mime_type": mime_type,
                "size_bytes": size_bytes,
                "event_type": event_type
            }
            
            _logger.debug(f"📋 Evento GCS parseado: {gcs_path} ({mime_type})")
            
            return result
        
        except Exception as e:
            _logger.error(f"❌ Error parseando evento GCS: {e}", exc_info=True)
            raise ValueError(f"Error parseando evento: {e}")
    
    def extract_metadata_from_path(self, gcs_path: str) -> Dict[str, str]:
        """
        Extrae metadata del path del archivo.
        
        Convención de paths:
        gs://bucket/users/{user_id}/chats/{chat_id}/raw/{upload_id}_{filename}
        
        Args:
            gcs_path: Ruta completa en GCS
        
        Returns:
            Diccionario con metadata extraída:
            {
                "user_id": "user123",
                "chat_id": "chat456",
                "upload_id": "uuid",
                "filename": "document.pdf"
            }
        """
        try:
            # Ejemplo: gs://bucket/users/user123/chats/chat456/raw/uuid_doc.pdf
            parts = gcs_path.replace("gs://", "").split("/")
            
            metadata = {}
            
            # Buscar user_id
            if "users" in parts:
                user_idx = parts.index("users")
                if user_idx + 1 < len(parts):
                    metadata["user_id"] = parts[user_idx + 1]
            
            # Buscar chat_id
            if "chats" in parts:
                chat_idx = parts.index("chats")
                if chat_idx + 1 < len(parts):
                    metadata["chat_id"] = parts[chat_idx + 1]
            
            # Filename (último componente)
            if parts:
                filename = parts[-1]
                metadata["filename"] = filename
                
                # Si filename tiene formato "uuid_originalname"
                if "_" in filename:
                    upload_id, original_name = filename.split("_", 1)
                    metadata["upload_id"] = upload_id
                    metadata["original_filename"] = original_name
            
            _logger.debug(f"📂 Metadata extraída del path: {metadata}")
            
            return metadata
        
        except Exception as e:
            _logger.error(f"❌ Error extrayendo metadata del path: {e}", exc_info=True)
            return {}


# Instancia singleton del router
_router_instance = None


def get_router() -> DocumentRouter:
    """
    Obtiene la instancia singleton del router.
    
    Returns:
        Instancia de DocumentRouter
    """
    global _router_instance
    if _router_instance is None:
        _router_instance = DocumentRouter()
    return _router_instance

