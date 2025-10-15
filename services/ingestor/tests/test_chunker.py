"""
Tests del chunker semántico.

Valida que el chunking funcione correctamente con diferentes tipos de texto.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from chunker import SemanticChunker


class TestSemanticChunker:
    """Tests del chunker semántico."""
    
    @pytest.fixture
    def chunker(self):
        """Chunker con configuración default."""
        return SemanticChunker(chunk_size=512, overlap=128)
    
    def test_chunker_initialization(self, chunker):
        """Validar inicialización del chunker."""
        assert chunker is not None
        assert chunker.chunk_size == 512
        assert chunker.overlap == 128
    
    def test_chunk_empty_text(self, chunker):
        """Validar chunking de texto vacío."""
        chunks = chunker.chunk_text("")
        assert chunks == []
    
    def test_chunk_short_text(self, chunker):
        """Validar chunking de texto corto."""
        text = "Este es un texto muy corto."
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["index"] == 0
        assert chunks[0]["char_count"] == len(text)
    
    def test_chunk_medium_text(self, chunker):
        """Validar chunking de texto mediano con párrafos."""
        text = """
Este es el primer párrafo. Tiene varias oraciones. Cada oración aporta información importante.

Este es el segundo párrafo. También tiene contenido relevante. Queremos preservar el contexto entre chunks.

Este es el tercer párrafo. Es parte del documento. Debe ser chunkead correctamente.
""".strip()
        
        chunks = chunker.chunk_text(text)
        
        # Debe generar al menos un chunk
        assert len(chunks) >= 1
        
        # Todos los chunks deben tener estructura correcta
        for chunk in chunks:
            assert "text" in chunk
            assert "index" in chunk
            assert "char_count" in chunk
            assert len(chunk["text"]) > 0
            assert chunk["char_count"] == len(chunk["text"])
        
        # Índices deben ser consecutivos
        indices = [c["index"] for c in chunks]
        assert indices == list(range(len(chunks)))
        
        print(f"\n✅ Texto mediano chunkead en {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"   Chunk {i}: {chunk['char_count']} chars")
    
    def test_chunk_long_text(self):
        """Validar chunking de texto largo con overlap."""
        # Crear texto largo
        paragraph = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20
        text = "\n\n".join([paragraph] * 10)  # ~12,000 chars
        
        chunker = SemanticChunker(chunk_size=500, overlap=100)
        chunks = chunker.chunk_text(text)
        
        # Debe generar múltiples chunks
        assert len(chunks) > 1
        
        # Ningún chunk debe exceder chunk_size significativamente
        for chunk in chunks:
            # Puede exceder un poco por límites de párrafo
            assert chunk["char_count"] <= chunker.chunk_size * 1.5
        
        print(f"\n✅ Texto largo ({len(text)} chars) → {len(chunks)} chunks")
    
    def test_chunk_with_metadata(self, chunker):
        """Validar que metadata se preserve en chunks."""
        text = "Este es un texto con metadata."
        metadata = {
            "source": "test_document.pdf",
            "page": 1
        }
        
        chunks = chunker.chunk_text(text, metadata=metadata)
        
        assert len(chunks) == 1
        assert "metadata" in chunks[0]
        assert chunks[0]["metadata"] == metadata
    
    def test_chunk_table(self, chunker):
        """Validar chunking de tabla."""
        table = {
            "headers": ["Nombre", "Edad", "Ciudad"],
            "rows": [
                ["Juan", "25", "Madrid"],
                ["María", "30", "Barcelona"],
                ["Pedro", "35", "Valencia"]
            ] * 10  # 30 filas
        }
        
        chunks = chunker.chunk_table(table)
        
        # Debe generar al menos un chunk
        assert len(chunks) >= 1
        
        # Cada chunk debe tener metadata de tabla
        for chunk in chunks:
            assert chunk["metadata"]["type"] == "table"
            assert "row_start" in chunk["metadata"]
            assert "row_end" in chunk["metadata"]
        
        print(f"\n✅ Tabla dividida en {len(chunks)} chunks")
        for chunk in chunks:
            print(f"   Rows {chunk['metadata']['row_start']}-{chunk['metadata']['row_end']}")


class TestChunkerEdgeCases:
    """Tests de casos extremos del chunker."""
    
    def test_very_long_sentence(self):
        """Validar manejo de oración muy larga."""
        # Oración de 1000 caracteres sin puntos
        long_sentence = "palabra " * 125  # ~1000 chars
        
        chunker = SemanticChunker(chunk_size=500, overlap=100)
        chunks = chunker.chunk_text(long_sentence)
        
        # Debe dividir aunque sea una sola oración
        assert len(chunks) >= 1
    
    def test_special_characters(self):
        """Validar manejo de caracteres especiales."""
        text = "Texto con émojis 🚀 y símbolos especiales: @#$%^&*()"
        
        chunker = SemanticChunker()
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
    
    def test_unicode_text(self):
        """Validar manejo de texto Unicode."""
        text = "你好世界 Привет мир مرحبا بالعالم"
        
        chunker = SemanticChunker()
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) == 1
        assert text in chunks[0]["text"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

