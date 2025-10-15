"""
Extractores de documentos para CorpChat Ingestor.

Cada extractor maneja un tipo de archivo específico:
- PDF: Texto, tablas, layout preservation
- DOCX: Word documents con formato  
- XLSX: Hojas de cálculo
- Image: OCR para extraer texto de imágenes
"""

from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .xlsx_extractor import XLSXExtractor
from .image_extractor import ImageExtractor

__all__ = [
    "PDFExtractor",
    "DOCXExtractor",
    "XLSXExtractor",
    "ImageExtractor"
]

# Factory para obtener extractor apropiado
def get_extractor(file_type: str):
    """
    Obtiene el extractor apropiado para un tipo de archivo.
    
    Args:
        file_type: "pdf", "docx", "xlsx", "image"
    
    Returns:
        Instancia del extractor correspondiente
    """
    extractors = {
        "pdf": PDFExtractor,
        "docx": DOCXExtractor,
        "doc": DOCXExtractor,
        "xlsx": XLSXExtractor,
        "xls": XLSXExtractor,
        "image": ImageExtractor
    }
    
    extractor_class = extractors.get(file_type.lower())
    if not extractor_class:
        raise ValueError(f"Extractor no disponible para tipo: {file_type}")
    
    return extractor_class()

