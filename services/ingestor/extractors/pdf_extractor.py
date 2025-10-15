"""
Extractor de PDF usando pdfplumber.

Extrae:
- Texto por página preservando layout
- Tablas con estructura
- Metadata (número de páginas, autor, etc.)
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
import pdfplumber

_logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extractor especializado para archivos PDF.
    
    Usa pdfplumber para:
    - Extracción de texto preservando layout
    - Detección y extracción de tablas
    - Metadata del documento
    """
    
    def __init__(self):
        """Inicializa el extractor PDF."""
        _logger.info("📄 PDFExtractor inicializado")
    
    def extract(self, pdf_path: str) -> Dict:
        """
        Extrae todo el contenido de un PDF.
        
        Args:
            pdf_path: Ruta local del archivo PDF
        
        Returns:
            Diccionario con:
            {
                "metadata": {...},
                "pages": [
                    {
                        "page": 1,
                        "text": "...",
                        "tables": [...]
                    },
                    ...
                ],
                "total_pages": 10,
                "extraction_method": "pdfplumber"
            }
        
        Raises:
            ValueError: Si el archivo no es válido
            FileNotFoundError: Si el archivo no existe
        """
        try:
            _logger.info(f"📖 Extrayendo PDF: {pdf_path}")
            
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"Archivo no encontrado: {pdf_path}")
            
            with pdfplumber.open(pdf_path) as pdf:
                # Extraer metadata
                metadata = pdf.metadata or {}
                total_pages = len(pdf.pages)
                
                _logger.debug(f"📊 PDF: {total_pages} páginas")
                
                # Extraer contenido por página
                pages = []
                for i, page in enumerate(pdf.pages, 1):
                    page_data = self._extract_page(page, i)
                    pages.append(page_data)
                
                result = {
                    "metadata": metadata,
                    "pages": pages,
                    "total_pages": total_pages,
                    "extraction_method": "pdfplumber"
                }
                
                _logger.info(
                    f"✅ PDF extraído: {total_pages} páginas, "
                    f"{sum(len(p['tables']) for p in pages)} tablas"
                )
                
                return result
        
        except Exception as e:
            _logger.error(f"❌ Error extrayendo PDF: {e}", exc_info=True)
            raise
    
    def _extract_page(self, page, page_num: int) -> Dict:
        """
        Extrae contenido de una página específica.
        
        Args:
            page: Objeto Page de pdfplumber
            page_num: Número de página (1-indexed)
        
        Returns:
            {
                "page": 1,
                "text": "...",
                "tables": [...],
                "width": 612,
                "height": 792
            }
        """
        try:
            # Extraer texto
            text = page.extract_text() or ""
            
            # Extraer tablas
            tables = []
            try:
                extracted_tables = page.extract_tables()
                for table in extracted_tables:
                    if table:
                        tables.append(self._format_table(table))
            except Exception as e:
                _logger.warning(f"⚠️ Error extrayendo tablas en página {page_num}: {e}")
            
            return {
                "page": page_num,
                "text": text.strip(),
                "tables": tables,
                "width": page.width,
                "height": page.height
            }
        
        except Exception as e:
            _logger.error(f"❌ Error en página {page_num}: {e}")
            return {
                "page": page_num,
                "text": "",
                "tables": [],
                "error": str(e)
            }
    
    def _format_table(self, table: List[List]) -> Dict:
        """
        Formatea una tabla extraída.
        
        Args:
            table: Tabla como lista de listas
        
        Returns:
            {
                "headers": [...],
                "rows": [[...]],
                "num_rows": 10,
                "num_cols": 5
            }
        """
        if not table or len(table) == 0:
            return {"headers": [], "rows": [], "num_rows": 0, "num_cols": 0}
        
        # Primera fila como headers
        headers = table[0] if table else []
        rows = table[1:] if len(table) > 1 else []
        
        return {
            "headers": [str(h) if h is not None else "" for h in headers],
            "rows": [
                [str(cell) if cell is not None else "" for cell in row]
                for row in rows
            ],
            "num_rows": len(rows),
            "num_cols": len(headers)
        }
    
    def extract_text(self, pdf_path: str) -> List[Dict]:
        """
        Extrae solo el texto (sin tablas), útil para RAG.
        
        Args:
            pdf_path: Ruta del PDF
        
        Returns:
            Lista de páginas con texto:
            [{"page": 1, "text": "..."}]
        """
        full_extraction = self.extract(pdf_path)
        return [
            {"page": p["page"], "text": p["text"]}
            for p in full_extraction["pages"]
        ]
    
    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """
        Extrae solo las tablas del PDF.
        
        Args:
            pdf_path: Ruta del PDF
        
        Returns:
            Lista de tablas con metadata:
            [{"page": 1, "table_index": 0, "table": {...}}]
        """
        full_extraction = self.extract(pdf_path)
        tables = []
        
        for page_data in full_extraction["pages"]:
            for i, table in enumerate(page_data["tables"]):
                tables.append({
                    "page": page_data["page"],
                    "table_index": i,
                    "table": table
                })
        
        return tables


if __name__ == "__main__":
    # Test básico
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        extractor = PDFExtractor()
        result = extractor.extract(sys.argv[1])
        print(f"\n✅ Extraído: {result['total_pages']} páginas")
        for page in result['pages'][:2]:  # Mostrar primeras 2 páginas
            print(f"\n=== Página {page['page']} ===")
            print(page['text'][:500])
            if page['tables']:
                print(f"\nTablas encontradas: {len(page['tables'])}")
    else:
        print("Uso: python pdf_extractor.py <ruta_pdf>")

