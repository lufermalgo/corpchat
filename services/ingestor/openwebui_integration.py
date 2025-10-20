"""
Integración con Open WebUI - Mapeo de parámetros
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class OpenWebUIConfig(BaseModel):
    """Configuración desde Open WebUI Admin Panel"""
    
    # General Settings
    content_extraction_engine: str = "corpchat"
    pdf_extract_images: bool = True
    bypass_embedding: bool = False
    text_splitter: str = "semantic"
    chunk_size: int = 1000
    chunk_overlap: int = 100
    
    # Embedding Settings
    embedding_model_engine: str = "vertex_ai"
    embedding_model: str = "text-embedding-004"
    
    # Retrieval Settings
    full_context_mode: bool = False
    hybrid_search: bool = True
    top_k: int = 3
    
    # File Settings
    allowed_extensions: list = ["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"]
    max_upload_size: Optional[int] = None
    max_upload_count: Optional[int] = None
    image_compression_width: Optional[int] = None
    image_compression_height: Optional[int] = None


def map_openwebui_to_corpchat(config: OpenWebUIConfig) -> Dict[str, Any]:
    """
    Mapea configuración de Open WebUI a parámetros de CorpChat
    
    Args:
        config: Configuración desde Open WebUI
        
    Returns:
        Diccionario con parámetros para CorpChat Pipeline
    """
    
    # Mapeo de parámetros
    corpchat_config = {
        # Pipeline Configuration
        "extraction_engine": "corpchat_specialized",
        "extractors": {
            "pdf": {
                "enabled": True,
                "ocr": config.pdf_extract_images,
                "extract_images": True
            },
            "docx": {"enabled": True},
            "xlsx": {"enabled": True},
            "images": {
                "enabled": True,
                "compression": {
                    "width": config.image_compression_width,
                    "height": config.image_compression_height
                }
            }
        },
        
        # Chunking Configuration
        "chunking": {
            "method": "semantic" if config.text_splitter == "semantic" else "character",
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "overlap_percentage": config.chunk_overlap / config.chunk_size if config.chunk_size > 0 else 0.1
        },
        
        # Embedding Configuration
        "embeddings": {
            "engine": "vertex_ai",
            "model": config.embedding_model,
            "dimensions": 768,
            "skip_embeddings": config.bypass_embedding
        },
        
        # Storage Configuration
        "storage": {
            "allowed_extensions": config.allowed_extensions,
            "max_upload_size": config.max_upload_size,
            "max_upload_count": config.max_upload_count,
            "compression": {
                "enabled": bool(config.image_compression_width or config.image_compression_height),
                "width": config.image_compression_width,
                "height": config.image_compression_height
            }
        },
        
        # Retrieval Configuration
        "retrieval": {
            "full_context_mode": config.full_context_mode,
            "hybrid_search": config.hybrid_search,
            "top_k": config.top_k,
            "vector_store": "bigquery"
        }
    }
    
    return corpchat_config


def create_openwebui_endpoint_config() -> Dict[str, Any]:
    """
    Configuración para endpoint de Open WebUI
    
    Returns:
        Configuración del endpoint
    """
    return {
        "endpoint": "/extract",
        "method": "POST",
        "content_type": "multipart/form-data",
        "response_format": "openwebui_compatible",
        "include_citations": True,
        "include_metadata": True
    }


# Configuración por defecto basada en Open WebUI
DEFAULT_OPENWEBUI_CONFIG = OpenWebUIConfig(
    chunk_size=1000,
    chunk_overlap=100,
    top_k=3,
    hybrid_search=True,
    allowed_extensions=["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"]
)
