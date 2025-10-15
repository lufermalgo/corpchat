"""
Extractor de Imágenes usando pytesseract (OCR).

Extrae:
- Texto via OCR (Tesseract)
- Layout básico
- Metadata de la imagen
- Fallback a Google Vision API (opcional)
"""

import logging
from typing import Dict, Optional
from pathlib import Path
from PIL import Image
import pytesseract

_logger = logging.getLogger(__name__)


class ImageExtractor:
    """
    Extractor especializado para imágenes (OCR).
    
    Usa pytesseract para:
    - Extracción de texto via OCR
    - Detección de layout básico
    - Metadata de la imagen
    
    Fallback opcional a Vision API para mejores resultados.
    """
    
    def __init__(self, use_vision_api: bool = False):
        """
        Inicializa el extractor de imágenes.
        
        Args:
            use_vision_api: Si True, usar Vision API; si False, pytesseract
        """
        self.use_vision_api = use_vision_api
        _logger.info(f"🖼️  ImageExtractor inicializado (Vision API: {use_vision_api})")
    
    def extract(self, image_path: str) -> Dict:
        """
        Extrae texto de una imagen usando OCR.
        
        Args:
            image_path: Ruta local de la imagen
        
        Returns:
            Diccionario con:
            {
                "metadata": {
                    "format": "PNG",
                    "size": [1920, 1080],
                    "mode": "RGB"
                },
                "text": "Texto extraído...",
                "confidence": 0.85,  # opcional si usa Vision API
                "extraction_method": "pytesseract|vision_api"
            }
        
        Raises:
            ValueError: Si el archivo no es válido
            FileNotFoundError: Si el archivo no existe
        """
        try:
            _logger.info(f"📖 Extrayendo imagen: {image_path}")
            
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Archivo no encontrado: {image_path}")
            
            # Abrir imagen
            img = Image.open(image_path)
            
            # Extraer metadata
            metadata = self._extract_metadata(img)
            
            # Extraer texto
            if self.use_vision_api:
                text, confidence = self._extract_with_vision_api(image_path)
                method = "vision_api"
            else:
                text, confidence = self._extract_with_tesseract(img)
                method = "pytesseract"
            
            result = {
                "metadata": metadata,
                "text": text.strip(),
                "confidence": confidence,
                "extraction_method": method
            }
            
            _logger.info(
                f"✅ Imagen extraída: {len(text)} caracteres "
                f"(método: {method}, confidence: {confidence:.2f})"
            )
            
            return result
        
        except Exception as e:
            _logger.error(f"❌ Error extrayendo imagen: {e}", exc_info=True)
            raise
    
    def _extract_metadata(self, img: Image.Image) -> Dict:
        """
        Extrae metadata de la imagen.
        
        Args:
            img: Objeto Image de PIL
        
        Returns:
            Metadata de la imagen
        """
        return {
            "format": img.format or "UNKNOWN",
            "size": list(img.size),
            "mode": img.mode,
            "width": img.width,
            "height": img.height
        }
    
    def _extract_with_tesseract(self, img: Image.Image) -> tuple[str, float]:
        """
        Extrae texto usando pytesseract.
        
        Args:
            img: Objeto Image de PIL
        
        Returns:
            (texto_extraido, confidence)
        """
        try:
            # Configuración de tesseract para español + inglés
            config = '--oem 3 --psm 6'  # OEM 3 = LSTM, PSM 6 = assume uniform block
            
            # Extraer texto
            text = pytesseract.image_to_string(
                img,
                lang='spa+eng',  # Español + Inglés
                config=config
            )
            
            # Intentar obtener confidence (puede fallar en algunas versiones)
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                confidences = [float(c) for c in data['conf'] if c != -1]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                avg_confidence = avg_confidence / 100.0  # Normalizar a 0-1
            except Exception as e:
                _logger.warning(f"⚠️ No se pudo obtener confidence: {e}")
                avg_confidence = 0.5  # Default
            
            return text, avg_confidence
        
        except Exception as e:
            _logger.error(f"❌ Error en Tesseract OCR: {e}", exc_info=True)
            return "", 0.0
    
    def _extract_with_vision_api(self, image_path: str) -> tuple[str, float]:
        """
        Extrae texto usando Google Vision API.
        
        Args:
            image_path: Ruta de la imagen
        
        Returns:
            (texto_extraido, confidence)
        """
        try:
            from google.cloud import vision
            
            client = vision.ImageAnnotatorClient()
            
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = client.text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            texts = response.text_annotations
            
            if not texts:
                return "", 0.0
            
            # El primer resultado es el texto completo
            full_text = texts[0].description
            
            # Calcular confidence promedio (Vision API no siempre provee)
            # Para OCR, la confidence es generalmente alta
            confidence = 0.9  # Default alto para Vision API
            
            return full_text, confidence
        
        except ImportError:
            _logger.error("❌ google-cloud-vision no instalado. Usar pytesseract")
            raise
        except Exception as e:
            _logger.error(f"❌ Error en Vision API: {e}", exc_info=True)
            return "", 0.0
    
    def extract_text(self, image_path: str) -> str:
        """
        Extrae solo el texto (sin metadata).
        
        Args:
            image_path: Ruta de la imagen
        
        Returns:
            Texto extraído
        """
        result = self.extract(image_path)
        return result["text"]


if __name__ == "__main__":
    # Test básico
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        # Intentar con tesseract por defecto
        extractor = ImageExtractor(use_vision_api=False)
        
        try:
            result = extractor.extract(sys.argv[1])
            print(f"\n✅ Imagen extraída:")
            print(f"   Método: {result['extraction_method']}")
            print(f"   Confidence: {result['confidence']:.2%}")
            print(f"   Dimensiones: {result['metadata']['width']}x{result['metadata']['height']}")
            print(f"\n📝 Texto extraído:")
            print(result['text'][:500] if result['text'] else "[Sin texto detectado]")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("\nNota: Asegúrate de tener Tesseract instalado:")
            print("  macOS: brew install tesseract tesseract-lang")
            print("  Ubuntu: apt-get install tesseract-ocr tesseract-ocr-spa")
    else:
        print("Uso: python image_extractor.py <ruta_imagen>")

