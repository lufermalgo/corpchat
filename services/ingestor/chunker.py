"""
Chunking semántico de documentos.

Divide documentos en chunks manejables preservando contexto semántico.
Usa overlap para mantener coherencia entre chunks.
"""

import logging
from typing import List, Dict, Optional
import re

_logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Divide texto en chunks semánticos con overlap.
    
    Estrategias:
    - Por párrafos y sentences para texto plano
    - Por filas para tablas
    - Overlap configurable para preservar contexto
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 128,
        min_chunk_size: int = 50
    ):
        """
        Inicializa el chunker.
        
        Args:
            chunk_size: Tamaño máximo de chunk en caracteres
            overlap: Overlap entre chunks en caracteres
            min_chunk_size: Tamaño mínimo para crear un chunk
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        
        _logger.info(
            f"✂️  SemanticChunker inicializado "
            f"(size={chunk_size}, overlap={overlap})"
        )
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Divide texto en chunks semánticos.
        
        Estrategia:
        1. Dividir por párrafos
        2. Agrupar párrafos hasta llegar a chunk_size
        3. Aplicar overlap entre chunks
        
        Args:
            text: Texto a dividir
            metadata: Metadata adicional para cada chunk
        
        Returns:
            Lista de chunks: [{"text": "...", "index": 0, "metadata": {...}}]
        """
        if not text or len(text) < self.min_chunk_size:
            if text:
                return [{
                    "text": text,
                    "index": 0,
                    "char_count": len(text),
                    "metadata": metadata or {}
                }]
            return []
        
        # Dividir por párrafos (doble salto de línea)
        paragraphs = re.split(r'\n\n+', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # Si el párrafo solo excede el límite, dividirlo por sentences
            if para_size > self.chunk_size:
                # Guardar chunk actual si existe
                if current_chunk:
                    chunks.append(self._create_chunk(
                        "\n\n".join(current_chunk),
                        chunk_index,
                        metadata
                    ))
                    chunk_index += 1
                    current_chunk = []
                    current_size = 0
                
                # Dividir párrafo largo por sentences
                sentence_chunks = self._chunk_long_paragraph(para, metadata)
                for sc in sentence_chunks:
                    sc["index"] = chunk_index
                    chunks.append(sc)
                    chunk_index += 1
                
                continue
            
            # Si agregar el párrafo excede el límite, guardar chunk actual
            if current_size + para_size > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(
                    "\n\n".join(current_chunk),
                    chunk_index,
                    metadata
                ))
                chunk_index += 1
                
                # Aplicar overlap: mantener último párrafo si cabe en overlap
                if para_size <= self.overlap:
                    current_chunk = [para]
                    current_size = para_size
                else:
                    current_chunk = []
                    current_size = 0
            
            # Agregar párrafo al chunk actual
            if not current_chunk or current_size == 0:
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size + 2  # +2 por \n\n
        
        # Guardar último chunk
        if current_chunk:
            chunks.append(self._create_chunk(
                "\n\n".join(current_chunk),
                chunk_index,
                metadata
            ))
        
        _logger.info(f"✅ Texto dividido en {len(chunks)} chunks")
        return chunks
    
    def _chunk_long_paragraph(
        self,
        para: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Divide un párrafo largo por sentences.
        
        Args:
            para: Párrafo largo
            metadata: Metadata
        
        Returns:
            Lista de chunks
        """
        # Dividir por sentences (punto + espacio + mayúscula)
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', para)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append({
                    "text": " ".join(current_chunk),
                    "char_count": current_size,
                    "metadata": metadata or {}
                })
                
                # Overlap: mantener última sentence si cabe
                if sentence_size <= self.overlap:
                    current_chunk = [sentence]
                    current_size = sentence_size
                else:
                    current_chunk = []
                    current_size = 0
            
            if not current_chunk:
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 1  # +1 por espacio
        
        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "char_count": current_size,
                "metadata": metadata or {}
            })
        
        return chunks
    
    def _create_chunk(
        self,
        text: str,
        index: int,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Crea un chunk con metadata.
        
        Args:
            text: Texto del chunk
            index: Índice del chunk
            metadata: Metadata adicional
        
        Returns:
            Chunk formateado
        """
        return {
            "text": text,
            "index": index,
            "char_count": len(text),
            "metadata": metadata or {}
        }
    
    def chunk_table(
        self,
        table: Dict,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Divide una tabla larga en chunks de filas.
        
        Estrategia:
        - Mantener headers en cada chunk
        - Agrupar filas hasta un límite razonable
        
        Args:
            table: Tabla con headers y rows
            metadata: Metadata adicional
        
        Returns:
            Lista de chunks de tabla
        """
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        
        if not rows:
            return []
        
        # Calcular cuántas filas caben en un chunk
        # Estimación: 50 chars por fila en promedio
        rows_per_chunk = max(5, self.chunk_size // 50)
        
        chunks = []
        for i in range(0, len(rows), rows_per_chunk):
            chunk_rows = rows[i:i + rows_per_chunk]
            
            # Formatear como texto
            text_parts = [" | ".join(headers)]
            for row in chunk_rows:
                text_parts.append(" | ".join(str(cell) for cell in row))
            
            chunk_text = "\n".join(text_parts)
            
            chunk_metadata = {
                "type": "table",
                "row_start": i,
                "row_end": i + len(chunk_rows),
                **(metadata or {})
            }
            
            chunks.append({
                "text": chunk_text,
                "index": len(chunks),
                "char_count": len(chunk_text),
                "metadata": chunk_metadata
            })
        
        _logger.info(f"✅ Tabla dividida en {len(chunks)} chunks")
        return chunks


if __name__ == "__main__":
    # Test básico
    logging.basicConfig(level=logging.INFO)
    
    # Test texto largo
    text = """
Este es el primer párrafo. Tiene varias oraciones. Cada oración aporta información.

Este es el segundo párrafo. También tiene contenido importante. Queremos preservar el contexto.

Este es el tercer párrafo. Es el último del ejemplo. Debería crear chunks apropiados.
""".strip()
    
    chunker = SemanticChunker(chunk_size=100, overlap=30)
    chunks = chunker.chunk_text(text)
    
    print(f"\n✅ Generados {len(chunks)} chunks:\n")
    for chunk in chunks:
        print(f"Chunk {chunk['index']} ({chunk['char_count']} chars):")
        print(f"  {chunk['text'][:80]}...")
        print()

