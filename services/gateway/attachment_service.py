"""
Servicio para recuperar y preparar adjuntos (imágenes) desde GCS/Firestore.

Este servicio implementa las mejores prácticas de ChatGPT/Gemini para el manejo de imágenes:
- Recupera imágenes desde Google Cloud Storage
- Convierte imágenes a formato base64 para envío a modelos multimodales
- Gestiona metadata de attachments en Firestore
"""

import logging
import base64
from typing import Optional, Dict, List
from google.cloud import storage, firestore
import mimetypes

_logger = logging.getLogger(__name__)


class AttachmentService:
    """
    Gestiona recuperación de adjuntos desde GCS y preparación para modelos multimodales.
    
    Responsabilidades:
    - Recuperar metadata de attachments desde Firestore
    - Descargar imágenes desde Google Cloud Storage
    - Convertir imágenes a formato base64 para envío a Gemini
    - Gestionar múltiples formatos de imagen
    """
    
    def __init__(self):
        """Inicializa el servicio de attachments."""
        self.storage_client = storage.Client()
        self.firestore_client = firestore.Client()
        _logger.info("AttachmentService inicializado")
    
    def get_attachment_metadata(self, chat_id: str, attachment_id: str) -> Optional[Dict]:
        """
        Obtiene metadata de attachment desde Firestore.
        
        Args:
            chat_id: ID del chat
            attachment_id: ID del attachment
            
        Returns:
            Diccionario con metadata del attachment o None si no existe
        """
        try:
            doc_ref = self.firestore_client.document(
                f"corpchat_chats/{chat_id}/attachments/{attachment_id}"
            )
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                _logger.info(f"Metadata obtenida para attachment {attachment_id}")
                return data
            else:
                _logger.warning(f"Attachment {attachment_id} no encontrado en Firestore")
                return None
                
        except Exception as e:
            _logger.error(f"Error obteniendo metadata de attachment {attachment_id}: {e}")
            return None
    
    def get_image_from_gcs(self, gcs_uri: str) -> Optional[bytes]:
        """
        Descarga imagen desde Google Cloud Storage.
        
        Args:
            gcs_uri: URI de GCS en formato gs://bucket/path
            
        Returns:
            Bytes de la imagen o None si hay error
        """
        try:
            # Parse gs://bucket/path
            if not gcs_uri.startswith("gs://"):
                _logger.error(f"URI no válida para GCS: {gcs_uri}")
                return None
                
            parts = gcs_uri.split('/')
            bucket_name = parts[2]
            blob_path = '/'.join(parts[3:])
            
            _logger.info(f"Descargando imagen: bucket={bucket_name}, path={blob_path}")
            
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            # Verificar que el blob existe
            if not blob.exists():
                _logger.error(f"Blob no existe: {gcs_uri}")
                return None
            
            image_bytes = blob.download_as_bytes()
            _logger.info(f"Imagen descargada exitosamente: {len(image_bytes)} bytes")
            
            return image_bytes
            
        except Exception as e:
            _logger.error(f"Error descargando imagen de GCS {gcs_uri}: {e}")
            return None
    
    def convert_to_base64_data_uri(self, image_bytes: bytes, mime_type: str) -> str:
        """
        Convierte imagen a formato data URI base64.
        
        Args:
            image_bytes: Bytes de la imagen
            mime_type: MIME type de la imagen (ej: image/png)
            
        Returns:
            String en formato data:image/...;base64,...
        """
        try:
            b64_data = base64.b64encode(image_bytes).decode('utf-8')
            data_uri = f"data:{mime_type};base64,{b64_data}"
            _logger.info(f"Imagen convertida a base64: {len(b64_data)} caracteres")
            return data_uri
        except Exception as e:
            _logger.error(f"Error convirtiendo imagen a base64: {e}")
            return ""
    
    def get_attachments_for_chat(self, chat_id: str) -> List[Dict]:
        """
        Obtiene todos los attachments de un chat.
        
        Args:
            chat_id: ID del chat
            
        Returns:
            Lista de diccionarios con metadata de attachments
        """
        try:
            attachments_ref = self.firestore_client.collection(
                f"corpchat_chats/{chat_id}/attachments"
            )
            attachments = [doc.to_dict() for doc in attachments_ref.stream()]
            _logger.info(f"Obtenidos {len(attachments)} attachments para chat {chat_id}")
            return attachments
        except Exception as e:
            _logger.error(f"Error obteniendo attachments para chat {chat_id}: {e}")
            return []
    
    def process_image_url(self, url: str, chat_id: Optional[str] = None) -> Optional[bytes]:
        """
        Procesa una URL de imagen y retorna los bytes.
        
        Args:
            url: URL de la imagen (puede ser GCS URI o API path)
            chat_id: ID del chat (opcional, para attachments de API)
            
        Returns:
            Bytes de la imagen o None si hay error
        """
        try:
            # Si es URL de GCS directa
            if url.startswith("gs://"):
                return self.get_image_from_gcs(url)
            
            # Si es path de API (/api/files/...)
            elif url.startswith("/api/files/"):
                if not chat_id:
                    _logger.error("chat_id requerido para procesar API path")
                    return None
                
                # Extraer attachment_id del path
                attachment_id = url.split("/")[-1]
                
                # Obtener metadata del attachment
                attachment_meta = self.get_attachment_metadata(chat_id, attachment_id)
                if not attachment_meta:
                    _logger.error(f"No se encontró metadata para attachment {attachment_id}")
                    return None
                
                # Obtener GCS URI de la metadata
                gcs_uri = attachment_meta.get("gcs_uri")
                if not gcs_uri:
                    _logger.error(f"No hay gcs_uri en metadata para attachment {attachment_id}")
                    return None
                
                return self.get_image_from_gcs(gcs_uri)
            
            else:
                _logger.warning(f"Formato de URL no soportado: {url}")
                return None
                
        except Exception as e:
            _logger.error(f"Error procesando URL de imagen {url}: {e}")
            return None
    
    def get_image_mime_type(self, url: str, attachment_meta: Optional[Dict] = None) -> str:
        """
        Determina el MIME type de una imagen.
        
        Args:
            url: URL o path de la imagen
            attachment_meta: Metadata del attachment (opcional)
            
        Returns:
            MIME type de la imagen
        """
        # Si tenemos metadata, usar el MIME type de ahí
        if attachment_meta and attachment_meta.get("mime_type"):
            return attachment_meta["mime_type"]
        
        # Si es URL de GCS, intentar deducir del path
        if url.startswith("gs://"):
            mime_type, _ = mimetypes.guess_type(url)
            return mime_type or "image/png"
        
        # Si es path de API, intentar deducir del path
        if url.startswith("/api/files/"):
            mime_type, _ = mimetypes.guess_type(url)
            return mime_type or "image/png"
        
        # Default
        return "image/png"
