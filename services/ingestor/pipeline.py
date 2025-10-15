"""
Pipeline de procesamiento completo de documentos.

Orquesta todo el flujo:
1. Download de GCS
2. Detección de tipo y extracción  
3. Chunking semántico
4. Generación de embeddings
5. Almacenamiento en BigQuery
6. Actualización de metadata en Firestore
"""

import logging
from typing import Dict, Optional
from pathlib import Path
import tempfile

from google.cloud import storage

from router import get_router
from extractors import get_extractor
from chunker import SemanticChunker
from embeddings import EmbeddingService
from storage_manager import StorageManager

_logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Pipeline completo de ingesta de documentos.
    
    Procesa documentos desde GCS hasta BigQuery Vector Search.
    """
    
    def __init__(self):
        """Inicializa el pipeline."""
        self.router = get_router()
        self.chunker = SemanticChunker(chunk_size=512, overlap=128)
        self.embedder = EmbeddingService()
        self.storage = StorageManager()
        self.gcs_client = storage.Client()
        
        _logger.info("🔄 IngestionPipeline inicializado")
    
    async def process_file(
        self,
        gcs_path: str,
        attachment_id: str,
        chat_id: str,
        user_id: str,
        mime_type: Optional[str] = None
    ) -> Dict:
        """
        Pipeline completo de procesamiento.
        
        Args:
            gcs_path: gs://bucket/path/to/file
            attachment_id: ID del attachment
            chat_id: ID del chat
            user_id: ID del usuario
            mime_type: Tipo MIME (opcional)
        
        Returns:
            Resultado del procesamiento:
            {
                "success": True,
                "chunks_stored": 10,
                "extraction_method": "pdfplumber",
                "processing_time_s": 5.2
            }
        """
        import time
        start_time = time.time()
        
        try:
            _logger.info(
                f"🚀 Iniciando pipeline: {gcs_path} "
                f"(attachment={attachment_id})"
            )
            
            # Actualizar estado a "processing"
            self.storage.update_attachment_metadata(
                attachment_id=attachment_id,
                chat_id=chat_id,
                status="processing"
            )
            
            # PASO 1: Download de GCS
            _logger.info("📥 Paso 1/6: Descargando de GCS...")
            local_path = self._download_from_gcs(gcs_path)
            
            # PASO 2: Determinar tipo y extraer
            _logger.info("🔍 Paso 2/6: Extrayendo contenido...")
            file_type = self.router.determine_extractor(gcs_path, mime_type)
            extractor = get_extractor(file_type)
            
            extracted_data = extractor.extract(local_path)
            extraction_method = extracted_data.get("extraction_method", file_type)
            
            # PASO 3: Convertir a texto plano para chunking
            _logger.info("📝 Paso 3/6: Preparando texto para chunking...")
            text_content = self._extract_text_content(extracted_data, file_type)
            
            # PASO 4: Chunking
            _logger.info("✂️  Paso 4/6: Generando chunks...")
            chunks = self.chunker.chunk_text(
                text_content,
                metadata={
                    "attachment_id": attachment_id,
                    "chat_id": chat_id,
                    "extraction_method": extraction_method,
                    "filename": Path(gcs_path).name
                }
            )
            
            _logger.info(f"   Chunks generados: {len(chunks)}")
            
            # PASO 5: Embeddings
            _logger.info("🧠 Paso 5/6: Generando embeddings...")
            chunks_with_embeddings = self.embedder.generate_for_chunks(chunks)
            
            # PASO 6: Almacenar en BigQuery
            _logger.info("💾 Paso 6/6: Almacenando en BigQuery...")
            storage_result = self.storage.store_chunks(
                chunks=chunks_with_embeddings,
                attachment_id=attachment_id,
                chat_id=chat_id,
                user_id=user_id
            )
            
            # Actualizar metadata como completado
            self.storage.mark_processing_complete(
                attachment_id=attachment_id,
                chat_id=chat_id,
                chunks_count=storage_result["chunks_stored"],
                extraction_method=extraction_method
            )
            
            # Cleanup temp file
            Path(local_path).unlink()
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "chunks_stored": storage_result["chunks_stored"],
                "extraction_method": extraction_method,
                "processing_time_s": round(processing_time, 2)
            }
            
            _logger.info(
                f"✅ Pipeline completado: {result['chunks_stored']} chunks "
                f"en {result['processing_time_s']}s"
            )
            
            return result
        
        except Exception as e:
            _logger.error(f"❌ Error en pipeline: {e}", exc_info=True)
            
            # Marcar como fallido
            self.storage.mark_processing_failed(
                attachment_id=attachment_id,
                chat_id=chat_id,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "processing_time_s": round(time.time() - start_time, 2)
            }
    
    def _download_from_gcs(self, gcs_path: str) -> str:
        """
        Descarga archivo de GCS a disco local temporal.
        
        Args:
            gcs_path: gs://bucket/path/to/file
        
        Returns:
            Ruta local del archivo descargado
        """
        # Parse GCS path
        if not gcs_path.startswith("gs://"):
            raise ValueError(f"Path inválido: {gcs_path}")
        
        path_parts = gcs_path.replace("gs://", "").split("/", 1)
        bucket_name = path_parts[0]
        blob_name = path_parts[1] if len(path_parts) > 1 else ""
        
        # Download
        bucket = self.gcs_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Crear archivo temporal preservando extensión
        suffix = Path(blob_name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            blob.download_to_filename(tmp.name)
            _logger.debug(f"📥 Descargado a: {tmp.name}")
            return tmp.name
    
    def _extract_text_content(self, extracted_data: Dict, file_type: str) -> str:
        """
        Extrae texto plano de datos extraídos.
        
        Args:
            extracted_data: Datos extraídos por el extractor
            file_type: Tipo de archivo
        
        Returns:
            Texto plano concatenado
        """
        if file_type == "pdf":
            # PDF: concatenar texto de todas las páginas
            pages = extracted_data.get("pages", [])
            return "\n\n".join(p.get("text", "") for p in pages)
        
        elif file_type in ["docx", "doc"]:
            # DOCX: concatenar secciones de texto
            sections = extracted_data.get("sections", [])
            text_parts = []
            for section in sections:
                if section["type"] in ["heading", "paragraph"]:
                    text_parts.append(section["text"])
            return "\n\n".join(text_parts)
        
        elif file_type in ["xlsx", "xls"]:
            # XLSX: concatenar todas las hojas
            sheets = extracted_data.get("sheets", [])
            text_parts = []
            for sheet in sheets:
                text_parts.append(f"=== {sheet['name']} ===")
                if sheet["headers"]:
                    text_parts.append(" | ".join(sheet["headers"]))
                for row in sheet["rows"]:
                    text_parts.append(" | ".join(row))
            return "\n".join(text_parts)
        
        elif file_type == "image":
            # Image: texto extraído por OCR
            return extracted_data.get("text", "")
        
        else:
            _logger.warning(f"⚠️ Tipo no soportado para extracción de texto: {file_type}")
            return ""


if __name__ == "__main__":
    # Test básico
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    async def test_pipeline():
        pipeline = IngestionPipeline()
        
        # Test con archivo de ejemplo (ajustar path)
        result = await pipeline.process_file(
            gcs_path="gs://corpchat-genai-385616-attachments/test.pdf",
            attachment_id="test_001",
            chat_id="chat_001",
            user_id="user_001",
            mime_type="application/pdf"
        )
        
        print(f"\n✅ Pipeline result: {result}")
    
    # asyncio.run(test_pipeline())
    print("Pipeline implementado. Ejecutar test_pipeline() para probar.")

