"""
Pipeline Processor - Procesador de Datos Multi-Modal.

Procesa diferentes tipos de datos: documentos, imágenes, datos estructurados
y no estructurados usando Google ADK y servicios de GCP.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, Optional
from datetime import datetime
import base64
import json

from google.adk.tools import FunctionTool
from google.cloud import documentai
from google.cloud import vision
from google.cloud import storage

from ..shared.types import ProcessedData
from ..shared.exceptions import PipelineError
from ..shared.utils import get_logger


class DataProcessor(ABC):
    """Patrón Strategy para procesadores de datos."""
    
    @abstractmethod
    async def process(self, data: Union[str, bytes], metadata: Dict[str, Any]) -> ProcessedData:
        """
        Procesa datos específicos.
        
        Args:
            data: Datos a procesar
            metadata: Metadatos adicionales
            
        Returns:
            Datos procesados
        """
        pass


class DocumentProcessor(DataProcessor):
    """Procesador de documentos usando Document AI."""
    
    def __init__(self, project_id: str, location: str = "us"):
        """
        Inicializa el procesador de documentos.
        
        Args:
            project_id: ID del proyecto GCP
            location: Ubicación del procesador
        """
        self.project_id = project_id
        self.location = location
        self.client = documentai.DocumentProcessorServiceClient()
        self.logger = get_logger("DocumentProcessor")
    
    async def process(self, data: bytes, metadata: Dict[str, Any]) -> ProcessedData:
        """
        Procesa documentos (PDF, DOCX, etc.).
        
        Args:
            data: Datos del documento
            metadata: Metadatos del documento
            
        Returns:
            Datos procesados
        """
        try:
            # Configurar procesador de documentos
            processor_name = f"projects/{self.project_id}/locations/{self.location}/processors/{metadata.get('processor_id', 'default')}"
            
            # Crear documento
            document = documentai.Document(
                content=data,
                mime_type=metadata.get("mime_type", "application/pdf")
            )
            
            # Procesar documento
            request = documentai.ProcessRequest(
                name=processor_name,
                document=document
            )
            
            result = self.client.process_document(request=request)
            document_result = result.document
            
            # Extraer texto y entidades
            processed_data = {
                "type": "document",
                "text": document_result.text,
                "entities": [
                    {
                        "type": entity.type_,
                        "mention_text": entity.mention_text,
                        "confidence": entity.confidence
                    }
                    for entity in document_result.entities
                ],
                "pages": len(document_result.pages),
                "language": document_result.language_code,
                "confidence": document_result.confidence,
                "metadata": metadata,
                "processed_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Documento procesado: {len(document_result.text)} caracteres")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error procesando documento: {e}")
            raise PipelineError(f"Error procesando documento: {e}")


class ImageProcessor(DataProcessor):
    """Procesador de imágenes usando Vision API."""
    
    def __init__(self, project_id: str):
        """
        Inicializa el procesador de imágenes.
        
        Args:
            project_id: ID del proyecto GCP
        """
        self.project_id = project_id
        self.client = vision.ImageAnnotatorClient()
        self.logger = get_logger("ImageProcessor")
    
    async def process(self, data: bytes, metadata: Dict[str, Any]) -> ProcessedData:
        """
        Procesa imágenes (PNG, JPG, etc.).
        
        Args:
            data: Datos de la imagen
            metadata: Metadatos de la imagen
            
        Returns:
            Datos procesados
        """
        try:
            # Crear imagen
            image = vision.Image(content=data)
            
            # Análisis completo de la imagen
            features = [
                vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION),
                vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION),
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION),
                vision.Feature(type_=vision.Feature.Type.FACE_DETECTION)
            ]
            
            # Procesar imagen
            response = self.client.annotate_image(
                request={"image": image, "features": features}
            )
            
            # Extraer información
            processed_data = {
                "type": "image",
                "text": [annotation.description for annotation in response.text_annotations],
                "labels": [
                    {
                        "description": label.description,
                        "score": label.score
                    }
                    for label in response.label_annotations
                ],
                "objects": [
                    {
                        "name": obj.name,
                        "score": obj.score,
                        "bounding_poly": [
                            {"x": vertex.x, "y": vertex.y}
                            for vertex in obj.bounding_poly.normalized_vertices
                        ]
                    }
                    for obj in response.localized_object_annotations
                ],
                "faces": len(response.face_annotations),
                "metadata": metadata,
                "processed_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Imagen procesada: {len(processed_data['text'])} textos detectados")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error procesando imagen: {e}")
            raise PipelineError(f"Error procesando imagen: {e}")


class StructuredDataProcessor(DataProcessor):
    """Procesador de datos estructurados."""
    
    def __init__(self):
        """Inicializa el procesador de datos estructurados."""
        self.logger = get_logger("StructuredDataProcessor")
    
    async def process(self, data: Union[str, bytes], metadata: Dict[str, Any]) -> ProcessedData:
        """
        Procesa datos estructurados (JSON, CSV, etc.).
        
        Args:
            data: Datos estructurados
            metadata: Metadatos
            
        Returns:
            Datos procesados
        """
        try:
            # Convertir a string si es necesario
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            # Determinar formato
            data_format = metadata.get("format", "json")
            
            if data_format == "json":
                parsed_data = json.loads(data)
            elif data_format == "csv":
                # Procesamiento básico de CSV
                lines = data.strip().split('\n')
                headers = lines[0].split(',')
                rows = [line.split(',') for line in lines[1:]]
                parsed_data = {
                    "headers": headers,
                    "rows": rows,
                    "row_count": len(rows)
                }
            else:
                parsed_data = {"raw": data}
            
            processed_data = {
                "type": "structured",
                "format": data_format,
                "data": parsed_data,
                "metadata": metadata,
                "processed_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Datos estructurados procesados: formato {data_format}")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error procesando datos estructurados: {e}")
            raise PipelineError(f"Error procesando datos estructurados: {e}")


class UnstructuredDataProcessor(DataProcessor):
    """Procesador de datos no estructurados."""
    
    def __init__(self):
        """Inicializa el procesador de datos no estructurados."""
        self.logger = get_logger("UnstructuredDataProcessor")
    
    async def process(self, data: Union[str, bytes], metadata: Dict[str, Any]) -> ProcessedData:
        """
        Procesa datos no estructurados (texto libre).
        
        Args:
            data: Datos no estructurados
            metadata: Metadatos
            
        Returns:
            Datos procesados
        """
        try:
            # Convertir a string si es necesario
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            # Análisis básico del texto
            words = data.split()
            sentences = data.split('.')
            
            processed_data = {
                "type": "unstructured",
                "text": data,
                "word_count": len(words),
                "sentence_count": len(sentences),
                "character_count": len(data),
                "language": metadata.get("language", "unknown"),
                "metadata": metadata,
                "processed_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Datos no estructurados procesados: {len(words)} palabras")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error procesando datos no estructurados: {e}")
            raise PipelineError(f"Error procesando datos no estructurados: {e}")


class PipelineProcessor:
    """
    Orquestador del pipeline de procesamiento.
    
    Coordina diferentes procesadores de datos según el tipo de input.
    """
    
    def __init__(self, config: Any):
        """
        Inicializa el Pipeline Processor.
        
        Args:
            config: Configuración del core
        """
        self.config = config
        self.logger = get_logger("PipelineProcessor")
        
        # Inicializar procesadores
        self.processors = {
            "document": DocumentProcessor(
                project_id=config.gcp_project_id,
                location=config.gcp_location
            ),
            "image": ImageProcessor(
                project_id=config.gcp_project_id
            ),
            "structured": StructuredDataProcessor(),
            "unstructured": UnstructuredDataProcessor()
        }
        
        self.logger.info("Pipeline Processor inicializado")
    
    async def process(self, input_data: Union[str, bytes], input_type: str) -> ProcessedData:
        """
        Procesa datos usando el procesador apropiado.
        
        Args:
            input_data: Datos de entrada
            input_type: Tipo de datos
            
        Returns:
            Datos procesados
        """
        try:
            processor = self.processors.get(input_type)
            if not processor:
                raise PipelineError(f"Tipo de input no soportado: {input_type}")
            
            # Metadatos básicos
            metadata = {
                "input_type": input_type,
                "size": len(input_data) if isinstance(input_data, bytes) else len(str(input_data)),
                "timestamp": datetime.now().isoformat()
            }
            
            # Procesar datos
            processed_data = await processor.process(input_data, metadata)
            
            self.logger.info(f"Datos procesados: tipo {input_type}")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error en pipeline de procesamiento: {e}")
            raise PipelineError(f"Error procesando datos: {e}")
    
    def get_capabilities(self) -> List[str]:
        """
        Retorna las capacidades del pipeline.
        
        Returns:
            Lista de tipos de datos soportados
        """
        return list(self.processors.keys())
    
    def get_processor_info(self, processor_type: str) -> Optional[Dict[str, Any]]:
        """
        Retorna información de un procesador específico.
        
        Args:
            processor_type: Tipo de procesador
            
        Returns:
            Información del procesador o None si no existe
        """
        if processor_type in self.processors:
            processor = self.processors[processor_type]
            return {
                "type": processor_type,
                "class": processor.__class__.__name__,
                "description": processor.__doc__ or "No description available"
            }
        return None


def create_pipeline_processor(config: Any) -> PipelineProcessor:
    """
    Crea una instancia del Pipeline Processor.
    
    Args:
        config: Configuración del core
        
    Returns:
        Instancia del Pipeline Processor
    """
    return PipelineProcessor(config)
