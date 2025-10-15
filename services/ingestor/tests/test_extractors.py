"""
Tests unitarios de extractores de documentos.

Valida que cada extractor funcione correctamente con documentos reales.
"""

import pytest
import sys
from pathlib import Path

# Agregar parent directory al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.pdf_extractor import PDFExtractor
from extractors.docx_extractor import DOCXExtractor
from extractors.xlsx_extractor import XLSXExtractor
from extractors.image_extractor import ImageExtractor


# Fixtures para paths de documentos canario
@pytest.fixture
def canary_dir():
    """Directorio con documentos canario."""
    return Path(__file__).parent / "canary"


@pytest.fixture
def pdf_simple(canary_dir):
    """Path al PDF simple."""
    pdf_path = canary_dir / "pdfs" / "test_simple.pdf"
    if not pdf_path.exists():
        pytest.skip(f"PDF simple no encontrado: {pdf_path}")
    return str(pdf_path)


@pytest.fixture
def pdf_with_table(canary_dir):
    """Path al PDF con tabla."""
    pdf_path = canary_dir / "pdfs" / "test_table.pdf"
    if not pdf_path.exists():
        pytest.skip(f"PDF con tabla no encontrado: {pdf_path}")
    return str(pdf_path)


@pytest.fixture
def xlsx_file(canary_dir):
    """Path al Excel."""
    xlsx_path = canary_dir / "xlsx" / "test_merged_cells.xlsx"
    if not xlsx_path.exists():
        pytest.skip(f"XLSX no encontrado: {xlsx_path}")
    return str(xlsx_path)


@pytest.fixture
def docx_file(canary_dir):
    """Path al DOCX."""
    docx_path = canary_dir / "docx" / "test_headings.docx"
    if not docx_path.exists():
        pytest.skip(f"DOCX no encontrado: {docx_path}")
    return str(docx_path)


@pytest.fixture
def image_file(canary_dir):
    """Path a la imagen."""
    img_path = canary_dir / "images" / "test_screenshot.png"
    if not img_path.exists():
        pytest.skip(f"Imagen no encontrada: {img_path}")
    return str(img_path)


# ==========================================
# Tests PDF Extractor
# ==========================================

class TestPDFExtractor:
    """Tests del extractor PDF."""
    
    def test_pdf_extractor_initialization(self):
        """Validar que el extractor se inicializa correctamente."""
        extractor = PDFExtractor()
        assert extractor is not None
    
    def test_extract_simple_pdf(self, pdf_simple):
        """Validar extracción de PDF simple."""
        extractor = PDFExtractor()
        result = extractor.extract(pdf_simple)
        
        # Validaciones básicas
        assert result is not None
        assert "pages" in result
        assert "total_pages" in result
        assert "extraction_method" in result
        
        # Validar que se extrajeron páginas
        assert result["total_pages"] > 0
        assert len(result["pages"]) == result["total_pages"]
        
        # Validar estructura de página
        first_page = result["pages"][0]
        assert "page" in first_page
        assert "text" in first_page
        assert first_page["page"] == 1
        
        # Validar que hay texto
        assert len(first_page["text"]) > 0
        
        print(f"\n✅ PDF simple extraído: {result['total_pages']} páginas")
        print(f"   Texto primera página: {len(first_page['text'])} chars")
    
    def test_extract_pdf_with_table(self, pdf_with_table):
        """Validar extracción de PDF con tabla."""
        extractor = PDFExtractor()
        result = extractor.extract(pdf_with_table)
        
        # Validar estructura básica
        assert result is not None
        assert len(result["pages"]) > 0
        
        # Buscar página con tabla
        tables_found = sum(len(p.get("tables", [])) for p in result["pages"])
        
        # Debe haber al menos una tabla
        assert tables_found > 0, "No se detectaron tablas en el PDF"
        
        # Validar estructura de tabla
        for page in result["pages"]:
            if page.get("tables"):
                table = page["tables"][0]
                assert "headers" in table
                assert "rows" in table
                assert "num_rows" in table
                assert "num_cols" in table
                
                print(f"\n✅ Tabla detectada: {table['num_rows']}x{table['num_cols']}")
                print(f"   Headers: {table['headers'][:3]}...")
                break
    
    def test_extract_text_only(self, pdf_simple):
        """Validar extracción solo de texto."""
        extractor = PDFExtractor()
        pages = extractor.extract_text(pdf_simple)
        
        assert len(pages) > 0
        assert all("text" in p for p in pages)
        
        total_text = " ".join(p["text"] for p in pages)
        assert len(total_text) > 100  # Al menos 100 caracteres


# ==========================================
# Tests DOCX Extractor
# ==========================================

class TestDOCXExtractor:
    """Tests del extractor DOCX."""
    
    def test_docx_extractor_initialization(self):
        """Validar que el extractor se inicializa correctamente."""
        extractor = DOCXExtractor()
        assert extractor is not None
    
    def test_extract_docx_with_headings(self, docx_file):
        """Validar extracción de DOCX con encabezados."""
        extractor = DOCXExtractor()
        result = extractor.extract(docx_file)
        
        # Validaciones básicas
        assert result is not None
        assert "sections" in result
        assert "extraction_method" in result
        
        # Validar que hay secciones
        assert len(result["sections"]) > 0
        
        # Buscar encabezados
        headings = [s for s in result["sections"] if s["type"] == "heading"]
        
        # Debe haber al menos un encabezado
        assert len(headings) > 0, "No se detectaron encabezados"
        
        # Validar estructura de encabezado
        first_heading = headings[0]
        assert "level" in first_heading
        assert "text" in first_heading
        assert 1 <= first_heading["level"] <= 6
        
        print(f"\n✅ DOCX extraído: {len(result['sections'])} secciones")
        print(f"   Encabezados encontrados: {len(headings)}")
        for h in headings[:3]:
            print(f"   H{h['level']}: {h['text'][:50]}...")
    
    def test_extract_text_from_docx(self, docx_file):
        """Validar extracción solo de texto."""
        extractor = DOCXExtractor()
        text = extractor.extract_text(docx_file)
        
        assert len(text) > 0
        assert isinstance(text, str)
        
        print(f"\n✅ Texto DOCX extraído: {len(text)} chars")


# ==========================================
# Tests XLSX Extractor
# ==========================================

class TestXLSXExtractor:
    """Tests del extractor XLSX."""
    
    def test_xlsx_extractor_initialization(self):
        """Validar que el extractor se inicializa correctamente."""
        extractor = XLSXExtractor()
        assert extractor is not None
    
    def test_extract_xlsx_with_merged_cells(self, xlsx_file):
        """Validar extracción de XLSX con merged cells."""
        extractor = XLSXExtractor()
        result = extractor.extract(xlsx_file)
        
        # Validaciones básicas
        assert result is not None
        assert "sheets" in result
        assert "total_sheets" in result
        
        # Validar que hay hojas
        assert result["total_sheets"] > 0
        assert len(result["sheets"]) > 0
        
        # Validar estructura de hoja
        first_sheet = result["sheets"][0]
        assert "name" in first_sheet
        assert "headers" in first_sheet
        assert "rows" in first_sheet
        assert "num_rows" in first_sheet
        assert "num_cols" in first_sheet
        
        print(f"\n✅ XLSX extraído: {result['total_sheets']} hojas")
        print(f"   Primera hoja: {first_sheet['num_rows']}x{first_sheet['num_cols']}")
        
        # Validar merged cells si existen
        if first_sheet.get("merged_cells"):
            print(f"   Merged cells detectadas: {len(first_sheet['merged_cells'])}")
            for mc in first_sheet["merged_cells"][:2]:
                print(f"     {mc['range']}: {mc['value'][:30]}...")
    
    def test_extract_sheet_as_table(self, xlsx_file):
        """Validar extracción de hoja específica como tabla."""
        extractor = XLSXExtractor()
        
        # Extraer primera hoja
        table = extractor.extract_sheet_as_table(xlsx_file, sheet_name=None)
        
        assert "headers" in table
        assert "rows" in table
        assert len(table["headers"]) > 0


# ==========================================
# Tests Image Extractor
# ==========================================

class TestImageExtractor:
    """Tests del extractor de imágenes (OCR)."""
    
    def test_image_extractor_initialization(self):
        """Validar que el extractor se inicializa correctamente."""
        extractor = ImageExtractor(use_vision_api=False)
        assert extractor is not None
    
    def test_extract_image_with_tesseract(self, image_file):
        """Validar extracción de imagen con Tesseract."""
        extractor = ImageExtractor(use_vision_api=False)
        
        try:
            result = extractor.extract(image_file)
            
            # Validaciones básicas
            assert result is not None
            assert "text" in result
            assert "metadata" in result
            assert "extraction_method" in result
            
            # Validar metadata de imagen
            metadata = result["metadata"]
            assert "width" in metadata
            assert "height" in metadata
            assert "format" in metadata
            
            # El texto puede estar vacío si no hay texto en la imagen
            # pero debe ser un string
            assert isinstance(result["text"], str)
            
            print(f"\n✅ Imagen extraída con OCR:")
            print(f"   Dimensiones: {metadata['width']}x{metadata['height']}")
            print(f"   Formato: {metadata['format']}")
            print(f"   Texto detectado: {len(result['text'])} chars")
            if result['text']:
                print(f"   Preview: {result['text'][:100]}...")
            
        except Exception as e:
            # Tesseract puede no estar instalado
            if "tesseract" in str(e).lower():
                pytest.skip(f"Tesseract no instalado: {e}")
            else:
                raise


# ==========================================
# Tests de Integración de Extractores
# ==========================================

class TestExtractorFactory:
    """Tests del factory de extractores."""
    
    def test_get_extractor_pdf(self):
        """Validar factory retorna PDFExtractor."""
        from extractors import get_extractor
        
        extractor = get_extractor("pdf")
        assert isinstance(extractor, PDFExtractor)
    
    def test_get_extractor_docx(self):
        """Validar factory retorna DOCXExtractor."""
        from extractors import get_extractor
        
        extractor = get_extractor("docx")
        assert isinstance(extractor, DOCXExtractor)
    
    def test_get_extractor_xlsx(self):
        """Validar factory retorna XLSXExtractor."""
        from extractors import get_extractor
        
        extractor = get_extractor("xlsx")
        assert isinstance(extractor, XLSXExtractor)
    
    def test_get_extractor_image(self):
        """Validar factory retorna ImageExtractor."""
        from extractors import get_extractor
        
        extractor = get_extractor("image")
        assert isinstance(extractor, ImageExtractor)
    
    def test_get_extractor_invalid_type(self):
        """Validar factory falla con tipo inválido."""
        from extractors import get_extractor
        
        with pytest.raises(ValueError):
            get_extractor("invalid_type")


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "-s"])

