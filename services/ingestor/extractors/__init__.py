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

