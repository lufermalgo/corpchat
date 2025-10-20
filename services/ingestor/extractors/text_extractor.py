"""
Extractor de texto plano para CorpChat Ingestor.

Extrae:
- Archivos de texto plano (.txt)
- Archivos CSV (.csv)
- Contenido directo sin procesamiento adicional
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

_logger = logging.getLogger(__name__)


class TextExtractor:
    """
    Extractor especializado para archivos de texto plano.
    
    Maneja:
    - Archivos .txt
    - Archivos .csv
    - Contenido directo
    """
    
    def __init__(self):
        """Inicializa el extractor de texto."""
        _logger.info("📝 TextExtractor inicializado")
    
    def extract(self, text_path: str) -> Dict:
        """
        Extrae contenido de un archivo de texto.
        
        Args:
            text_path: Ruta del archivo de texto
        
        Returns:
            Diccionario con:
            {
                "metadata": {...},
                "content": "texto completo",
                "extraction_method": "text"
            }
        
        Raises:
            ValueError: Si el archivo no es válido
            FileNotFoundError: Si el archivo no existe
        """
        try:
            _logger.info(f"📖 Extrayendo texto: {text_path}")
            
            if not Path(text_path).exists():
                raise FileNotFoundError(f"Archivo no encontrado: {text_path}")
            
            # Leer contenido del archivo
            with open(text_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Extraer metadata básico
            metadata = {
                "filename": Path(text_path).name,
                "size": len(content),
                "lines": len(content.splitlines()),
                "encoding": "utf-8"
            }
            
            result = {
                "metadata": metadata,
                "content": content,
                "extraction_method": "text"
            }
            
            _logger.info(
                f"✅ Texto extraído: {len(content)} caracteres, {metadata['lines']} líneas"
            )
            
            return result
        
        except Exception as e:
            _logger.error(f"❌ Error extrayendo texto: {e}", exc_info=True)
            raise
    
    def extract_all_text(self, text_path: str) -> str:
        """
        Extrae todo el texto del archivo (compatible con otros extractores).
        
        Args:
            text_path: Ruta del archivo de texto
        
        Returns:
            Texto completo del archivo
        """
        result = self.extract(text_path)
        return result["content"]


if __name__ == "__main__":
    # Test básico
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        extractor = TextExtractor()
        result = extractor.extract(sys.argv[1])
        print(f"\n✅ Extraído: {result['metadata']['size']} caracteres")
        print(f"📄 Líneas: {result['metadata']['lines']}")
        print(f"📝 Contenido: {result['content'][:100]}...")
    else:
        print("Uso: python text_extractor.py <ruta_texto>")
