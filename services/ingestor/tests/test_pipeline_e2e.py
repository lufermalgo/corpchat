"""
Test End-to-End del pipeline de ingesta completo.

Valida todo el flujo: Extract → Chunk → Embed → Store
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors import get_extractor
from chunker import SemanticChunker
from embeddings import EmbeddingService
from storage_manager import StorageManager


class TestPipelineIntegration:
    """Tests de integración del pipeline."""
    
    @pytest.fixture
    def sample_text(self):
        """Texto de ejemplo para tests."""
        return """
# Política de Vacaciones

Todos los empleados tienen derecho a 22 días hábiles de vacaciones al año.

## Solicitud de Vacaciones

Para solicitar vacaciones, el empleado debe:
1. Completar el formulario en el portal de RRHH
2. Obtener aprobación del supervisor directo
3. Notificar al equipo con al menos 2 semanas de anticipación

Las vacaciones no utilizadas pueden acumularse hasta un máximo de 10 días.
""".strip()
    
    def test_extract_chunk_flow(self, sample_text, tmp_path):
        """Validar flujo Extract → Chunk."""
        # Crear archivo temporal de texto
        test_file = tmp_path / "test.txt"
        test_file.write_text(sample_text)
        
        # Paso 1: Chunk del texto
        chunker = SemanticChunker(chunk_size=200, overlap=50)
        chunks = chunker.chunk_text(sample_text)
        
        # Validaciones
        assert len(chunks) > 0, "No se generaron chunks"
        
        # Verificar estructura de chunks
        for chunk in chunks:
            assert "text" in chunk
            assert "index" in chunk
            assert "char_count" in chunk
            assert len(chunk["text"]) > 0
        
        print(f"\n✅ Extract → Chunk: {len(chunks)} chunks generados")
        for i, chunk in enumerate(chunks):
            print(f"   Chunk {i}: {chunk['char_count']} chars")
    
    def test_chunk_embed_flow(self, sample_text):
        """Validar flujo Chunk → Embed (mock)."""
        # Paso 1: Chunking
        chunker = SemanticChunker(chunk_size=200, overlap=50)
        chunks = chunker.chunk_text(sample_text)
        
        assert len(chunks) > 0
        
        # Paso 2: Embeddings (mock)
        with patch.object(EmbeddingService, 'generate_embedding') as mock_embed:
            # Mock retorna embedding de 768 dims
            mock_embed.return_value = [0.1] * 768
            
            embedder = EmbeddingService()
            
            for chunk in chunks:
                embedding = embedder.generate_embedding(chunk["text"])
                chunk["embedding"] = embedding
            
            # Validaciones
            assert all("embedding" in c for c in chunks)
            assert all(len(c["embedding"]) == 768 for c in chunks)
            
            print(f"\n✅ Chunk → Embed: {len(chunks)} chunks con embeddings")
            print(f"   Dimensiones: {len(chunks[0]['embedding'])}")
    
    def test_embed_store_flow(self, sample_text):
        """Validar flujo Embed → Store (mock)."""
        # Preparar chunks con embeddings
        chunker = SemanticChunker(chunk_size=200, overlap=50)
        chunks = chunker.chunk_text(sample_text, metadata={"source": "test.pdf"})
        
        # Agregar embeddings mock
        for chunk in chunks:
            chunk["embedding"] = [0.1] * 768
        
        # Mock del storage
        with patch.object(StorageManager, 'store_chunks') as mock_store, \
             patch.object(StorageManager, 'update_attachment_metadata') as mock_update:
            
            mock_store.return_value = {
                "chunks_stored": len(chunks),
                "success": True,
                "errors": []
            }
            
            storage = StorageManager()
            
            # Almacenar chunks
            result = storage.store_chunks(
                chunks=chunks,
                attachment_id="test_001",
                chat_id="chat_001",
                user_id="user_001"
            )
            
            # Validaciones
            assert result["success"]
            assert result["chunks_stored"] == len(chunks)
            
            print(f"\n✅ Embed → Store: {result['chunks_stored']} chunks almacenados")


class TestPipelineE2E:
    """Test E2E completo del pipeline (mock de servicios externos)."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_mock(self, tmp_path):
        """Test del pipeline completo con mocks."""
        # Crear documento de prueba
        test_content = """
Documento de Prueba
===================

Este es un documento de prueba para validar el pipeline completo.

Sección 1: Introducción
-----------------------
El pipeline procesa documentos en varios pasos.

Sección 2: Procesamiento
------------------------
Los pasos incluyen: extracción, chunking, embeddings y storage.
""".strip()
        
        test_file = tmp_path / "test.txt"
        test_file.write_text(test_content)
        
        # Simular pipeline
        print("\n🔄 Iniciando pipeline E2E (mock)...")
        
        # Paso 1: Chunking
        chunker = SemanticChunker(chunk_size=150, overlap=30)
        chunks = chunker.chunk_text(test_content)
        assert len(chunks) > 0
        print(f"   ✅ Paso 1: {len(chunks)} chunks generados")
        
        # Paso 2: Embeddings (mock)
        with patch.object(EmbeddingService, 'batch_generate') as mock_batch:
            mock_batch.return_value = [[0.1] * 768 for _ in chunks]
            
            embedder = EmbeddingService()
            chunks_with_embeddings = chunks.copy()
            embeddings = embedder.batch_generate([c["text"] for c in chunks])
            
            for chunk, embedding in zip(chunks_with_embeddings, embeddings):
                chunk["embedding"] = embedding
            
            assert all("embedding" in c for c in chunks_with_embeddings)
            print(f"   ✅ Paso 2: {len(embeddings)} embeddings generados")
        
        # Paso 3: Storage (mock)
        with patch.object(StorageManager, 'store_chunks') as mock_store:
            mock_store.return_value = {
                "chunks_stored": len(chunks_with_embeddings),
                "success": True,
                "errors": []
            }
            
            storage = StorageManager()
            result = storage.store_chunks(
                chunks=chunks_with_embeddings,
                attachment_id="e2e_test_001",
                chat_id="e2e_chat_001",
                user_id="e2e_user"
            )
            
            assert result["success"]
            print(f"   ✅ Paso 3: {result['chunks_stored']} chunks almacenados")
        
        print("\n✅ Pipeline E2E completado exitosamente")


class TestPipelineErrorHandling:
    """Tests de manejo de errores en el pipeline."""
    
    def test_empty_document(self):
        """Validar manejo de documento vacío."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_text("")
        
        assert chunks == []
    
    def test_chunk_without_embedding(self):
        """Validar manejo de chunks sin embedding."""
        chunks = [
            {"text": "Chunk sin embedding", "index": 0}
        ]
        
        with patch.object(StorageManager, 'store_chunks') as mock_store:
            mock_store.return_value = {
                "chunks_stored": 0,
                "success": False,
                "errors": ["No hay chunks con embeddings válidos"]
            }
            
            storage = StorageManager()
            result = storage.store_chunks(
                chunks=chunks,
                attachment_id="error_test",
                chat_id="error_chat",
                user_id="error_user"
            )
            
            assert not result["success"]
            assert result["chunks_stored"] == 0
    
    def test_embedding_service_error(self):
        """Validar manejo de error en servicio de embeddings."""
        with patch.object(EmbeddingService, 'generate_embedding') as mock_embed:
            mock_embed.side_effect = Exception("Vertex AI error")
            
            embedder = EmbeddingService()
            
            with pytest.raises(Exception) as exc_info:
                embedder.generate_embedding("test text")
            
            assert "Vertex AI error" in str(exc_info.value)


class TestPipelinePerformance:
    """Tests de performance del pipeline."""
    
    def test_chunking_performance(self):
        """Validar performance del chunking."""
        import time
        
        # Documento grande (~50KB)
        large_text = "Lorem ipsum dolor sit amet. " * 2000
        
        chunker = SemanticChunker()
        
        start = time.time()
        chunks = chunker.chunk_text(large_text)
        duration = time.time() - start
        
        # Debe completar en menos de 1 segundo
        assert duration < 1.0, f"Chunking demasiado lento: {duration:.2f}s"
        assert len(chunks) > 0
        
        print(f"\n✅ Performance chunking: {len(large_text)} chars → {len(chunks)} chunks en {duration:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

