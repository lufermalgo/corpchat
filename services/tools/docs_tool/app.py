"""
Docs Tool - Herramienta para leer documentos de GCS y Google Drive.

Proporciona endpoints OpenAPI para que los agentes ADK lean documentos corporativos.
"""

import logging
import os
from typing import Optional
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from google.cloud import storage
from google.cloud import logging as cloud_logging

# Configurar logging
cloud_logging.Client().setup_logging()
_logger = logging.getLogger(__name__)

# Variables de entorno
PROJECT_ID = os.getenv("PROJECT_ID", "genai-385616")
GCS_BUCKET = os.getenv("GCS_BUCKET", f"corpchat-{PROJECT_ID}-attachments")

# FastAPI app
app = FastAPI(
    title="CorpChat Docs Tool",
    description="Herramienta para leer documentos corporativos",
    version="1.0.0"
)

# Cliente GCS
storage_client = storage.Client()


# Modelos Pydantic
class ReadDocumentRequest(BaseModel):
    """Request para leer un documento."""
    path: str
    user_id: Optional[str] = None


class ReadDocumentResponse(BaseModel):
    """Response con el contenido del documento."""
    content: str
    path: str
    size_bytes: int
    content_type: str


class GetSignedUrlRequest(BaseModel):
    """Request para obtener URL firmada."""
    path: str
    user_id: Optional[str] = None
    expires_minutes: int = 15


class GetSignedUrlResponse(BaseModel):
    """Response con URL firmada."""
    signed_url: str
    path: str
    expires_in_minutes: int


def extract_user_from_header(header_value: Optional[str]) -> str:
    """Extrae user ID desde header IAP."""
    if not header_value:
        return "anonymous"
    if ":" in header_value:
        return header_value.split(":")[-1]
    return header_value


def validate_user_access(user_id: str, path: str) -> bool:
    """
    Valida que el usuario tenga acceso al path.
    
    En MVP: validación básica por prefijos.
    En producción: consultar permisos en Firestore.
    
    Args:
        user_id: ID del usuario
        path: Path del documento
    
    Returns:
        True si tiene acceso
    """
    # MVP: permitir acceso a paths que incluyan el user_id
    # o que estén en carpetas públicas
    
    if "public/" in path:
        return True
    
    if f"users/{user_id}/" in path:
        return True
    
    # TODO: Implementar validación completa con Firestore
    _logger.warning(f"Acceso no validado: user={user_id}, path={path}")
    return True  # Por ahora permitir (MVP)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "corpchat-docs-tool",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/read", response_model=ReadDocumentResponse)
async def read_document(
    request: ReadDocumentRequest,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Lee un documento de GCS.
    
    Args:
        request: Request con path del documento
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        Contenido del documento
    """
    try:
        user_id = extract_user_from_header(x_goog_authenticated_user_email)
        if request.user_id:
            user_id = request.user_id
        
        # Validar acceso
        if not validate_user_access(user_id, request.path):
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Leer de GCS
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(request.path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Descargar contenido
        content = blob.download_as_text()
        
        _logger.info(
            f"Documento leído: {request.path} por {user_id}",
            extra={"user_id": user_id, "path": request.path}
        )
        
        return ReadDocumentResponse(
            content=content,
            path=request.path,
            size_bytes=blob.size,
            content_type=blob.content_type or "text/plain"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error leyendo documento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/signed-url", response_model=GetSignedUrlResponse)
async def get_signed_url(
    request: GetSignedUrlRequest,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Genera una URL firmada para acceso temporal a un documento.
    
    Args:
        request: Request con path y tiempo de expiración
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        URL firmada
    """
    try:
        user_id = extract_user_from_header(x_goog_authenticated_user_email)
        if request.user_id:
            user_id = request.user_id
        
        # Validar acceso
        if not validate_user_access(user_id, request.path):
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Generar URL firmada
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(request.path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=request.expires_minutes),
            method="GET"
        )
        
        _logger.info(
            f"URL firmada generada: {request.path} para {user_id}",
            extra={"user_id": user_id, "path": request.path}
        )
        
        return GetSignedUrlResponse(
            signed_url=signed_url,
            path=request.path,
            expires_in_minutes=request.expires_minutes
        )
    
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error generando URL firmada: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list")
async def list_documents(
    prefix: str = "",
    limit: int = 100,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Lista documentos en GCS.
    
    Args:
        prefix: Prefijo de path para filtrar
        limit: Número máximo de resultados
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        Lista de documentos
    """
    try:
        user_id = extract_user_from_header(x_goog_authenticated_user_email)
        
        # Validar acceso al prefijo
        if not validate_user_access(user_id, prefix):
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Listar blobs
        bucket = storage_client.bucket(GCS_BUCKET)
        blobs = bucket.list_blobs(prefix=prefix, max_results=limit)
        
        documents = []
        for blob in blobs:
            documents.append({
                "name": blob.name,
                "size_bytes": blob.size,
                "content_type": blob.content_type,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "public_url": blob.public_url if blob.public_url else None
            })
        
        _logger.info(
            f"Documentos listados: prefix={prefix}, count={len(documents)}",
            extra={"user_id": user_id, "prefix": prefix}
        )
        
        return {
            "documents": documents,
            "count": len(documents),
            "prefix": prefix
        }
    
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error listando documentos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

