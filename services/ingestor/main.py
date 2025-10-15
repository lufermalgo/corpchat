"""
Servicio Ingestor de CorpChat - Document Processing Pipeline.

Este servicio procesa archivos adjuntos (PDF, DOCX, XLSX, imágenes):
1. Recibe notificaciones Pub/Sub de nuevos archivos en GCS
2. Extrae texto y estructura (tablas, encabezados)
3. Genera chunks semánticos con overlap
4. Crea embeddings con Vertex AI
5. Almacena en BigQuery para vector search
6. Actualiza metadata en Firestore

Endpoints:
- POST /process: Procesar archivo manualmente
- GET /status/{job_id}: Estado de procesamiento
- GET /health: Health check
"""

import logging
import os
import uuid
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from google.cloud import logging as cloud_logging

# Configurar logging
cloud_logging.Client().setup_logging()
_logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="CorpChat Ingestor",
    description="Document Processing Pipeline",
    version="1.0.0"
)

# Job tracking (en memoria para MVP, migrar a Firestore/Redis para producción)
processing_jobs = {}


class ProcessRequest(BaseModel):
    """Request para procesar un archivo manualmente."""
    gcs_path: str
    attachment_id: str
    chat_id: str
    user_id: str
    mime_type: Optional[str] = None


class JobStatus(BaseModel):
    """Estado de un job de procesamiento."""
    job_id: str
    status: str  # pending, processing, completed, failed
    gcs_path: str
    attachment_id: str
    progress: float  # 0.0 - 1.0
    chunks_processed: int
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "corpchat-ingestor",
        "version": "1.0.0",
        "status": "healthy",
        "components": {
            "extractors": ["pdf", "docx", "xlsx", "image"],
            "chunking": "semantic",
            "embeddings": "text-embedding-004",
            "storage": "bigquery"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "extractors_available": True,
        "storage_available": True
    }


@app.post("/process")
async def process_file(
    request: ProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Procesa un archivo manualmente (bypass Pub/Sub).
    
    Args:
        request: Información del archivo a procesar
        background_tasks: Para procesamiento asíncrono
    
    Returns:
        Job ID para tracking
    """
    try:
        job_id = str(uuid.uuid4())
        
        _logger.info(
            f"📝 Nuevo job de procesamiento: {job_id}",
            extra={
                "job_id": job_id,
                "gcs_path": request.gcs_path,
                "attachment_id": request.attachment_id,
                "chat_id": request.chat_id
            }
        )
        
        # Crear registro de job
        processing_jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "gcs_path": request.gcs_path,
            "attachment_id": request.attachment_id,
            "chat_id": request.chat_id,
            "user_id": request.user_id,
            "progress": 0.0,
            "chunks_processed": 0,
            "started_at": datetime.now()
        }
        
        # Agregar tarea de procesamiento en background
        background_tasks.add_task(
            process_document_async,
            job_id=job_id,
            gcs_path=request.gcs_path,
            attachment_id=request.attachment_id,
            chat_id=request.chat_id,
            user_id=request.user_id,
            mime_type=request.mime_type
        )
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Procesamiento iniciado"
        }
    
    except Exception as e:
        _logger.error(f"❌ Error creando job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Obtiene el estado de un job de procesamiento.
    
    Args:
        job_id: ID del job
    
    Returns:
        Estado actual del job
    """
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    return processing_jobs[job_id]


async def process_document_async(
    job_id: str,
    gcs_path: str,
    attachment_id: str,
    chat_id: str,
    user_id: str,
    mime_type: Optional[str] = None
):
    """
    Procesa un documento de forma asíncrona.
    
    Pipeline completo:
    1. Download de GCS
    2. Detectar tipo y extraer
    3. Chunking semántico
    4. Generar embeddings
    5. Almacenar en BigQuery
    6. Actualizar Firestore
    
    Args:
        job_id: ID del job para tracking
        gcs_path: Ruta del archivo en GCS
        attachment_id: ID del attachment
        chat_id: ID del chat
        user_id: ID del usuario
        mime_type: Tipo MIME del archivo (opcional)
    """
    try:
        _logger.info(f"🔄 Iniciando procesamiento: {job_id}")
        
        # Actualizar estado
        processing_jobs[job_id]["status"] = "processing"
        processing_jobs[job_id]["progress"] = 0.1
        
        # TODO: Implementar pipeline completo
        # Por ahora, placeholder para MVP
        
        # Simular procesamiento (será reemplazado por pipeline real)
        import asyncio
        await asyncio.sleep(2)
        
        # Actualizar estado final
        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["progress"] = 1.0
        processing_jobs[job_id]["chunks_processed"] = 0  # Placeholder
        processing_jobs[job_id]["completed_at"] = datetime.now()
        
        _logger.info(f"✅ Procesamiento completado: {job_id}")
    
    except Exception as e:
        _logger.error(f"❌ Error en procesamiento {job_id}: {e}", exc_info=True)
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)
        processing_jobs[job_id]["completed_at"] = datetime.now()


@app.post("/webhook/pubsub")
async def pubsub_webhook(
    request: dict,
    background_tasks: BackgroundTasks
):
    """
    Webhook para recibir notificaciones Pub/Sub de GCS.
    
    Cloud Storage publica eventos cuando se crea un archivo.
    Este endpoint los recibe y dispatch al pipeline.
    
    Args:
        request: Payload de Pub/Sub
        background_tasks: Para procesamiento asíncrono
    
    Returns:
        Confirmación de recepción
    """
    try:
        # Extraer datos del evento Pub/Sub
        # Formato: https://cloud.google.com/storage/docs/pubsub-notifications
        
        # TODO: Implementar parsing de evento Pub/Sub
        # TODO: Validar firma y autenticación
        # TODO: Extraer gcs_path, attachment_id, chat_id, user_id
        
        _logger.info(f"📨 Evento Pub/Sub recibido: {request}")
        
        return {"status": "received"}
    
    except Exception as e:
        _logger.error(f"❌ Error procesando evento Pub/Sub: {e}", exc_info=True)
        # Retornar 200 para evitar reintents de Pub/Sub
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    
    _logger.info(f"🚀 Iniciando Ingestor en puerto {port}")
    _logger.info(f"📊 Pipeline: Extract → Chunk → Embed → Store (BigQuery)")
    
    uvicorn.run(app, host="0.0.0.0", port=port)

