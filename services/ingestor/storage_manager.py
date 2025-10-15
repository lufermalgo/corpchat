"""
Storage Manager para BigQuery y Firestore.

Orquesta el almacenamiento de chunks con embeddings en BigQuery
y actualización de metadata en Firestore.
"""

import logging
from typing import List, Dict
import sys
from pathlib import Path

# Agregar parent directory al path para imports
parent_path = Path(__file__).parent.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

from agents.shared.bigquery_vector_search import BigQueryVectorSearch
from agents.shared.firestore_client import FirestoreClient

_logger = logging.getLogger(__name__)


class StorageManager:
    """
    Gestiona almacenamiento de chunks procesados.
    
    Responsabilidades:
    - Almacenar chunks con embeddings en BigQuery
    - Actualizar metadata de attachments en Firestore
    - Tracking de estado de procesamiento
    """
    
    def __init__(self):
        """Inicializa el storage manager."""
        self.bq = BigQueryVectorSearch()
        self.firestore = FirestoreClient()
        _logger.info("💾 StorageManager inicializado")
    
    def store_chunks(
        self,
        chunks: List[Dict],
        attachment_id: str,
        chat_id: str,
        user_id: str
    ) -> Dict:
        """
        Almacena chunks con embeddings en BigQuery.
        
        Args:
            chunks: Lista de chunks con "text" y "embedding"
            attachment_id: ID del attachment
            chat_id: ID del chat
            user_id: ID del usuario
        
        Returns:
            Resultado del almacenamiento:
            {
                "chunks_stored": 10,
                "success": True,
                "errors": []
            }
        """
        if not chunks:
            _logger.warning("⚠️ No hay chunks para almacenar")
            return {
                "chunks_stored": 0,
                "success": True,
                "errors": []
            }
        
        try:
            _logger.info(
                f"💾 Almacenando {len(chunks)} chunks en BigQuery "
                f"(attachment={attachment_id})"
            )
            
            # Preparar chunks para BigQuery
            bq_chunks = []
            for i, chunk in enumerate(chunks):
                if "embedding" not in chunk:
                    _logger.warning(f"⚠️ Chunk {i} sin embedding, skip")
                    continue
                
                bq_chunk = {
                    "chunk_id": f"{attachment_id}_{i}",
                    "attachment_id": attachment_id,
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "text": chunk["text"],
                    "embedding": chunk["embedding"],
                    "page": chunk.get("metadata", {}).get("page"),
                    "source_filename": chunk.get("metadata", {}).get("filename"),
                    "chunk_index": i,
                    "extraction_method": chunk.get("metadata", {}).get("extraction_method")
                }
                
                bq_chunks.append(bq_chunk)
            
            # Insertar en BigQuery
            if bq_chunks:
                self.bq.insert_chunks(bq_chunks)
                
                _logger.info(f"✅ {len(bq_chunks)} chunks almacenados en BigQuery")
                
                return {
                    "chunks_stored": len(bq_chunks),
                    "success": True,
                    "errors": []
                }
            else:
                return {
                    "chunks_stored": 0,
                    "success": False,
                    "errors": ["No hay chunks con embeddings válidos"]
                }
        
        except Exception as e:
            _logger.error(f"❌ Error almacenando chunks: {e}", exc_info=True)
            return {
                "chunks_stored": 0,
                "success": False,
                "errors": [str(e)]
            }
    
    def update_attachment_metadata(
        self,
        attachment_id: str,
        chat_id: str,
        status: str,
        metadata: Dict = None
    ):
        """
        Actualiza metadata del attachment en Firestore.
        
        Args:
            attachment_id: ID del attachment
            chat_id: ID del chat
            status: Estado (processing, ready, failed)
            metadata: Metadata adicional (chunks_count, etc.)
        """
        try:
            attachment_path = f"corpchat_chats/{chat_id}/attachments/{attachment_id}"
            
            update_data = {
                "status": status,
                "updated_at": self.firestore.get_server_timestamp()
            }
            
            if metadata:
                update_data.update(metadata)
            
            self.firestore.set_document(attachment_path, update_data, merge=True)
            
            _logger.info(
                f"✅ Metadata actualizada: attachment={attachment_id}, "
                f"status={status}"
            )
        
        except Exception as e:
            _logger.error(f"❌ Error actualizando metadata: {e}", exc_info=True)
    
    def mark_processing_complete(
        self,
        attachment_id: str,
        chat_id: str,
        chunks_count: int,
        extraction_method: str
    ):
        """
        Marca procesamiento como completado.
        
        Args:
            attachment_id: ID del attachment
            chat_id: ID del chat
            chunks_count: Número de chunks generados
            extraction_method: Método de extracción usado
        """
        self.update_attachment_metadata(
            attachment_id=attachment_id,
            chat_id=chat_id,
            status="ready",
            metadata={
                "chunks_count": chunks_count,
                "extraction_method": extraction_method,
                "processed_at": self.firestore.get_server_timestamp()
            }
        )
    
    def mark_processing_failed(
        self,
        attachment_id: str,
        chat_id: str,
        error: str
    ):
        """
        Marca procesamiento como fallido.
        
        Args:
            attachment_id: ID del attachment
            chat_id: ID del chat
            error: Mensaje de error
        """
        self.update_attachment_metadata(
            attachment_id=attachment_id,
            chat_id=chat_id,
            status="failed",
            metadata={
                "error": error,
                "failed_at": self.firestore.get_server_timestamp()
            }
        )


if __name__ == "__main__":
    # Test básico
    logging.basicConfig(level=logging.INFO)
    
    manager = StorageManager()
    
    # Test con chunks de ejemplo
    test_chunks = [
        {
            "text": "Este es un chunk de prueba",
            "embedding": [0.1] * 768,  # Embedding dummy
            "metadata": {
                "page": 1,
                "filename": "test.pdf",
                "extraction_method": "pdfplumber"
            }
        }
    ]
    
    result = manager.store_chunks(
        chunks=test_chunks,
        attachment_id="test_attach_001",
        chat_id="test_chat_001",
        user_id="test_user"
    )
    
    print(f"\n✅ Test result: {result}")

