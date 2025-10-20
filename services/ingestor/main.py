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

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Request
from pydantic import BaseModel
import uvicorn
from google.cloud import logging as cloud_logging
from openwebui_integration import OpenWebUIConfig, map_openwebui_to_corpchat

# ==========================================
# CONFIGURACIÓN DE ENTORNO LOCAL
# ==========================================
IS_LOCAL = os.getenv("ENVIRONMENT", "production") == "local"

# Configurar logging
try:
    cloud_logging.Client().setup_logging()
except Exception as e:
    print(f"Warning: Could not setup cloud logging: {e}")

logging.basicConfig(level=logging.INFO)
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


@app.get("/files/{user_id}")
async def get_user_files(user_id: str):
    """
    Lista todos los archivos cargados por un usuario específico.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Lista de archivos con metadata
    """
    try:
        _logger.info(f"Obteniendo archivos para usuario: {user_id}")
        
        # Listar archivos en Cloud Storage
        from google.cloud import storage
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
        storage_client = storage.Client(project=project_id)
        bucket_name = os.getenv("GCS_BUCKET_ATTACHMENTS")
        if not bucket_name:
            raise ValueError("GCS_BUCKET_ATTACHMENTS environment variable is required")
        bucket = storage_client.bucket(bucket_name)
        
        # Buscar archivos del usuario
        prefix = f"openwebui/{user_id}/"
        blobs = bucket.list_blobs(prefix=prefix)
        
        files = []
        for blob in blobs:
            # Extraer nombre original del archivo
            filename = blob.name.split('/')[-1]
            # Remover UUID del nombre
            if '_' in filename:
                original_name = '_'.join(filename.split('_')[1:])
            else:
                original_name = filename
            
            files.append({
                "filename": original_name,
                "storage_path": blob.name,
                "size": blob.size,
                "created": blob.time_created.isoformat(),
                "content_type": blob.content_type,
                "gcs_url": f"gs://{bucket_name}/{blob.name}"
            })
        
        # Ordenar por fecha de creación (más recientes primero)
        files.sort(key=lambda x: x["created"], reverse=True)
        
        _logger.info(f"Encontrados {len(files)} archivos para usuario {user_id}")
        
        return {
            "user_id": user_id,
            "files_count": len(files),
            "files": files
        }
        
    except Exception as e:
        _logger.error(f"Error obteniendo archivos del usuario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/re-read/{user_id}")
async def re_read_document(
    user_id: str,
    filename: str,
    force_refresh: bool = False
):
    """
    Re-lee un documento específico del usuario.
    
    Args:
        user_id: ID del usuario
        filename: Nombre del archivo a re-leer
        force_refresh: Si True, fuerza la actualización incluso si ya existe
        
    Returns:
        Resultado del re-procesamiento
    """
    try:
        _logger.info(f"Re-leyendo documento: {filename} para usuario: {user_id}")
        
        # Buscar el archivo en Cloud Storage
        from google.cloud import storage
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
        storage_client = storage.Client(project=project_id)
        bucket_name = os.getenv("GCS_BUCKET_ATTACHMENTS")
        if not bucket_name:
            raise ValueError("GCS_BUCKET_ATTACHMENTS environment variable is required")
        bucket = storage_client.bucket(bucket_name)
        
        # Buscar archivo específico
        prefix = f"openwebui/{user_id}/"
        blobs = list(bucket.list_blobs(prefix=prefix))
        
        target_blob = None
        for blob in blobs:
            if filename in blob.name:
                target_blob = blob
                break
        
        if not target_blob:
            raise HTTPException(status_code=404, detail=f"Archivo {filename} no encontrado para usuario {user_id}")
        
        _logger.info(f"Archivo encontrado: {target_blob.name}")
        
        # Descargar archivo temporalmente
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
            target_blob.download_to_filename(temp_file.name)
            temp_path = temp_file.name
        
        # Procesar archivo usando el pipeline completo
        from pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        
        # Generar nuevos IDs
        import uuid
        attachment_id = str(uuid.uuid4())
        chat_id = f"re_read_{user_id}_{int(datetime.now().timestamp())}"
        
        # Procesar archivo
        result = pipeline.process_file(
            gcs_path=f"gs://{bucket_name}/{target_blob.name}",
            attachment_id=attachment_id,
            chat_id=chat_id,
            user_id=user_id,
            mime_type=target_blob.content_type or "application/octet-stream"
        )
        
        # Limpiar archivo temporal
        os.unlink(temp_path)
        
        _logger.info(f"Documento re-leído exitosamente: {result}")
        
        return {
            "success": True,
            "message": f"Documento {filename} re-leído exitosamente",
            "attachment_id": attachment_id,
            "chat_id": chat_id,
            "chunks_created": result.get("chunks_stored", 0),
            "processing_time": result.get("processing_time_s", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error re-leyendo documento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


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
    Procesa un documento de forma asíncrona usando el pipeline completo.
    
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
        
        # Importar pipeline
        from pipeline import IngestionPipeline
        from openwebui_integration import OpenWebUIConfig, map_openwebui_to_corpchat, DEFAULT_OPENWEBUI_CONFIG
        
        # Ejecutar pipeline
        pipeline = IngestionPipeline()
        result = await pipeline.process_file(
            gcs_path=gcs_path,
            attachment_id=attachment_id,
            chat_id=chat_id,
            user_id=user_id,
            mime_type=mime_type
        )
        
        # Actualizar estado final
        if result["success"]:
            processing_jobs[job_id]["status"] = "completed"
            processing_jobs[job_id]["progress"] = 1.0
            processing_jobs[job_id]["chunks_processed"] = result["chunks_stored"]
            processing_jobs[job_id]["extraction_method"] = result["extraction_method"]
            processing_jobs[job_id]["processing_time_s"] = result["processing_time_s"]
            processing_jobs[job_id]["completed_at"] = datetime.now()
            
            _logger.info(
                f"✅ Procesamiento completado: {job_id} "
                f"({result['chunks_stored']} chunks en {result['processing_time_s']}s)"
            )
        else:
            processing_jobs[job_id]["status"] = "failed"
            processing_jobs[job_id]["error"] = result.get("error", "Unknown error")
            processing_jobs[job_id]["completed_at"] = datetime.now()
            
            _logger.error(f"❌ Procesamiento fallido: {job_id} - {result.get('error')}")
    
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


@app.post("/extract/process")
@app.put("/extract/process")
async def extract_for_openwebui_process(
    request: Request
):
    """
    Endpoint específico para Open WebUI (/extract/process).
    Implementa el protocolo oficial de Open WebUI External Document Loader.
    
    Open WebUI envía:
    - PUT request a /process
    - Headers: Content-Type, Authorization: Bearer {API_KEY}, X-Filename
    - Body: datos binarios del archivo
    """
    try:
        _logger.info("Open WebUI External Document Loader request recibida")
        
        # Verificar método HTTP
        if request.method == "PUT":
            # Protocolo oficial de Open WebUI External Document Loader
            _logger.info("Procesando request PUT (protocolo oficial Open WebUI)")
            
            # Obtener headers
            content_type = request.headers.get("content-type", "")
            authorization = request.headers.get("authorization", "")
            x_filename = request.headers.get("x-filename", "")
            
            _logger.info(f"Headers - Content-Type: {content_type}")
            _logger.info(f"Headers - Authorization: {authorization[:20]}...")
            _logger.info(f"Headers - X-Filename: {x_filename}")
            
            # Verificar autorización
            if not authorization.startswith("Bearer "):
                _logger.error("Authorization header faltante o inválido")
                raise HTTPException(status_code=401, detail="Authorization required")
            
            api_key = authorization[7:]  # Remove "Bearer "
            if api_key != "corpchat-local":
                _logger.error(f"API key inválida: {api_key}")
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            # Obtener datos binarios del archivo
            body = await request.body()
            if not body:
                _logger.error("No se recibieron datos del archivo")
                raise HTTPException(status_code=422, detail="No file data provided")
            
            _logger.info(f"Datos del archivo recibidos: {len(body)} bytes")
            
            # Crear UploadFile desde datos binarios
            from fastapi import UploadFile
            import io
            
            # Determinar filename
            filename = x_filename or "document.bin"
            if not filename:
                # Intentar determinar desde Content-Type
                if "pdf" in content_type.lower():
                    filename = "document.pdf"
                elif "docx" in content_type.lower():
                    filename = "document.docx"
                elif "xlsx" in content_type.lower():
                    filename = "document.xlsx"
                else:
                    filename = "document.bin"
            
            # Crear UploadFile
            file_obj = io.BytesIO(body)
            upload_file = UploadFile(
                filename=filename,
                file=file_obj,
                size=len(body)
            )
            
            _logger.info(f"Archivo creado: {filename} ({len(body)} bytes)")
            
            # Parámetros por defecto para Open WebUI
            user_id = "openwebui_user"
            chunk_size = 1000
            chunk_overlap = 100
            top_k = 3
            hybrid_search = True
            bypass_embedding = False
            
            # Procesar directamente sin pipeline completo (para Open WebUI)
            _logger.info("Procesando archivo directamente para Open WebUI")
            
            # Leer contenido del archivo
            content = await upload_file.read()
            
            # Determinar tipo de archivo
            file_extension = upload_file.filename.split('.')[-1].lower() if '.' in upload_file.filename else ''
            
            # Extraer texto usando extractores especializados
            extracted_text = ""
            if file_extension == 'txt':
                extracted_text = content.decode('utf-8')
            elif file_extension == 'pdf':
                # Para PDF, extraer texto básico (sin OCR por ahora)
                try:
                    import PyPDF2
                    import io
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                    extracted_text = "\n".join([page.extract_text() for page in pdf_reader.pages])
                except Exception as e:
                    _logger.warning(f"No se pudo extraer texto del PDF: {e}")
                    extracted_text = f"[PDF - {upload_file.filename} - Extracción de texto no disponible]"
            elif file_extension in ['xlsx', 'xls']:
                # Para Excel, usar XLSXExtractor
                try:
                    import tempfile
                    import os
                    from extractors.xlsx_extractor import XLSXExtractor
                    
                    # Guardar archivo temporalmente
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                        temp_file.write(content)
                        temp_path = temp_file.name
                    
                    # Extraer usando XLSXExtractor
                    extractor = XLSXExtractor()
                    extracted_text = extractor.extract_all_text(temp_path)
                    
                    # Limpiar archivo temporal
                    os.unlink(temp_path)
                    
                except Exception as e:
                    _logger.warning(f"No se pudo extraer texto del XLSX: {e}")
                    extracted_text = f"[XLSX - {upload_file.filename} - Error en extracción: {str(e)}]"
            elif file_extension in ['docx', 'doc']:
                # Para Word, usar DOCXExtractor
                try:
                    import tempfile
                    import os
                    from extractors.docx_extractor import DOCXExtractor
                    
                    # Guardar archivo temporalmente
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                        temp_file.write(content)
                        temp_path = temp_file.name
                    
                    # Extraer usando DOCXExtractor
                    extractor = DOCXExtractor()
                    extracted_text = extractor.extract_all_text(temp_path)
                    
                    # Limpiar archivo temporal
                    os.unlink(temp_path)
                    
                except Exception as e:
                    _logger.warning(f"No se pudo extraer texto del DOCX: {e}")
                    extracted_text = f"[DOCX - {upload_file.filename} - Error en extracción: {str(e)}]"
            elif file_extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']:
                # Para imágenes, usar ImageExtractor
                try:
                    import tempfile
                    import os
                    from extractors.image_extractor import ImageExtractor
                    
                    # Guardar archivo temporalmente
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                        temp_file.write(content)
                        temp_path = temp_file.name
                    
                    # Extraer usando ImageExtractor
                    extractor = ImageExtractor()
                    result = extractor.extract(temp_path)
                    extracted_text = result.get("text", "")
                    
                    # Limpiar archivo temporal
                    os.unlink(temp_path)
                    
                except Exception as e:
                    _logger.warning(f"No se pudo extraer texto de la imagen: {e}")
                    extracted_text = f"[Imagen - {upload_file.filename} - Error en OCR: {str(e)}]"
            else:
                extracted_text = f"[Archivo {file_extension.upper()} - {upload_file.filename} - Formato no soportado]"
            
            _logger.info(f"Texto extraído: {len(extracted_text)} caracteres")
            
            # PASO EXTRA: Guardar archivo original en Cloud Storage
            _logger.info("📦 Guardando archivo original en Cloud Storage...")
            try:
                from google.cloud import storage
                
                # Crear cliente de Cloud Storage
                storage_client = storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT", "genai-385616"))
                bucket_name = os.getenv("GCS_BUCKET_ATTACHMENTS")
                if not bucket_name:
                    raise ValueError("GCS_BUCKET_ATTACHMENTS environment variable is required")
                bucket = storage_client.bucket(bucket_name)
                
                # Crear ruta GCS
                gcs_filename = f"openwebui/{user_id}/{upload_file.filename}"
                blob = bucket.blob(gcs_filename)
                
                # Subir archivo
                blob.upload_from_string(content, content_type=content_type)
                
                _logger.info(f"📦 Archivo guardado en Cloud Storage: gs://{bucket_name}/{gcs_filename}")
                
            except Exception as e:
                _logger.error(f"❌ Error guardando archivo en Cloud Storage: {e}", exc_info=True)
            
            # Si bypass_embedding es False, generar embeddings
            if not bypass_embedding:
                try:
                    # Generar embedding del texto usando Vertex AI directamente
                    import vertexai
                    from vertexai.language_models import TextEmbeddingModel
                    
                    vertexai.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"), location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"))
                    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
                    
                    # Chunking simple
                    chunk_size_actual = min(chunk_size, len(extracted_text))
                    chunks = [extracted_text[i:i+chunk_size_actual] for i in range(0, len(extracted_text), chunk_size_actual - chunk_overlap)]
                    
                    _logger.info(f"Generando embeddings para {len(chunks)} chunks")
                    
                    # Generar embeddings para cada chunk
                    for i, chunk in enumerate(chunks):
                        # Generar embedding usando Vertex AI
                        embeddings = embedding_model.get_embeddings([chunk])
                        embedding = embeddings[0].values
                        
                        # Guardar en BigQuery usando BigQuery directamente
                        from google.cloud import bigquery
                        
                        client = bigquery.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
                        table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.corpchat.embeddings"
                        
                        # Generar IDs únicos
                        chunk_id = f"openwebui_{user_id}_{upload_file.filename}_{i}_{int(datetime.now().timestamp())}"
                        attachment_id = f"openwebui_{upload_file.filename}_{int(datetime.now().timestamp())}"
                        chat_id = f"openwebui_chat_{user_id}_{int(datetime.now().timestamp())}"
                        
                        # Insertar en BigQuery con esquema correcto
                        row_to_insert = {
                            "chunk_id": chunk_id,
                            "attachment_id": attachment_id,
                            "chat_id": chat_id,
                            "user_id": user_id,
                            "text": chunk,
                            "embedding": embedding,
                            "source_filename": upload_file.filename,
                            "chunk_index": i,
                            "extraction_method": "xlsx_extractor",
                            "created_at": datetime.now().isoformat()
                        }
                        
                        errors = client.insert_rows_json(table_id, [row_to_insert])
                        if errors:
                            _logger.error(f"Error insertando en BigQuery: {errors}")
                        else:
                            _logger.info(f"Chunk {i} insertado en BigQuery")
                    
                    _logger.info("Embeddings generados y guardados en BigQuery")
                    
                except Exception as e:
                    _logger.error(f"Error generando embeddings: {e}", exc_info=True)
            
            # Retornar formato esperado por Open WebUI
            return {
                "page_content": extracted_text,
                "metadata": {
                    "filename": upload_file.filename,
                    "size": len(content),
                    "chunks": len(extracted_text) // chunk_size + 1,
                    "embeddings_ready": not bypass_embedding,
                    "source": "corpchat-ingestor"
                }
            }
            
        else:
            # Fallback para requests POST (form data)
            _logger.info("Procesando request POST (form data)")
            
            form_data = await request.form()
            _logger.info(f"Form data keys: {list(form_data.keys())}")
            
            # Buscar archivo en diferentes campos posibles
            file = None
            for key in ['file', 'document', 'attachment', 'upload']:
                if key in form_data:
                    file = form_data[key]
                    _logger.info(f"Archivo encontrado en campo: {key}")
                    break
            
            if not file:
                _logger.error("No se encontró archivo en la request")
                raise HTTPException(status_code=422, detail="No file provided")
            
            # Crear UploadFile compatible
            from fastapi import UploadFile
            upload_file = UploadFile(
                filename=file.filename,
                file=file.file
            )
            
            # Obtener parámetros con defaults
            user_id = form_data.get("user_id", "openwebui_user")
            chunk_size = int(form_data.get("chunk_size", "1000"))
            chunk_overlap = int(form_data.get("chunk_overlap", "100"))
            top_k = int(form_data.get("top_k", "3"))
            hybrid_search = form_data.get("hybrid_search", "true").lower() == "true"
            bypass_embedding = form_data.get("bypass_embedding", "false").lower() == "true"
            
            return await extract_for_openwebui(
                upload_file, user_id, chunk_size, chunk_overlap, 
                top_k, hybrid_search, bypass_embedding
            )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error en extract_for_openwebui_process: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/extract")
async def extract_for_openwebui(
    file: UploadFile = File(...),
    user_id: str = Form(default="openwebui_user"),
    chunk_size: int = Form(default=1000),
    chunk_overlap: int = Form(default=100),
    top_k: int = Form(default=3),
    hybrid_search: bool = Form(default=True),
    bypass_embedding: bool = Form(default=False)
):
    """
    Endpoint específico para Open WebUI.
    Procesa documento y retorna formato compatible con Open WebUI.
    """
    try:
        _logger.info(f"Open WebUI extraction request: {file.filename}")
        
        # Crear configuración desde parámetros de Open WebUI
        openwebui_config = OpenWebUIConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            hybrid_search=hybrid_search,
            bypass_embedding=bypass_embedding
        )
        
        # Mapear a configuración de CorpChat
        corpchat_config = map_openwebui_to_corpchat(openwebui_config)
        
        # Procesar archivo temporalmente
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            
            # Importar pipeline
            from pipeline import IngestionPipeline
            
            # Ejecutar pipeline con configuración de Open WebUI
            pipeline = IngestionPipeline()
            result = await pipeline.process_file(
                gcs_path=temp_file.name,  # Ahora _download_from_gcs maneja paths locales
                attachment_id=str(uuid.uuid4()),
                chat_id="openwebui_chat",
                user_id=user_id,
                config=corpchat_config
            )
            
            # Limpiar archivo temporal DESPUÉS del procesamiento
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                _logger.warning(f"No se pudo eliminar archivo temporal: {e}")
            
            # Retornar formato compatible con Open WebUI
            return {
                "success": True,
                "content": result.get("extracted_text", ""),
                "chunks": len(result.get("chunks", [])),
                "metadata": {
                    "filename": file.filename,
                    "size": len(content),
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "embeddings_ready": not bypass_embedding
                },
                "citations": result.get("chunks", [])[:top_k] if result.get("chunks") else [],
                "vector_store": "bigquery"
            }
            
    except Exception as e:
        _logger.error(f"Error in Open WebUI extraction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/admin/reset-upload-directory")
async def reset_upload_directory():
    """Reset upload directory (Danger Zone)"""
    try:
        # Limpiar bucket de uploads temporales
        from google.cloud import storage
        client = storage.Client()
        bucket_name = os.getenv("GCS_BUCKET_ATTACHMENTS")
        if not bucket_name:
            raise ValueError("GCS_BUCKET_ATTACHMENTS environment variable is required")
        bucket = client.bucket(bucket_name)
        
        # Eliminar archivos temporales (prefijo temp_)
        blobs = bucket.list_blobs(prefix="temp_")
        deleted_count = 0
        for blob in blobs:
            blob.delete()
            deleted_count += 1
            
        _logger.info(f"Reset upload directory: {deleted_count} temp files deleted")
        
        return {
            "success": True,
            "message": f"Upload directory reset: {deleted_count} temp files deleted",
            "deleted_files": deleted_count
        }
        
    except Exception as e:
        _logger.error(f"Error resetting upload directory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@app.post("/admin/reset-vector-storage")
async def reset_vector_storage():
    """Reset vector storage and knowledge base (Danger Zone)"""
    try:
        from google.cloud import bigquery, firestore
        
        # Limpiar embeddings de BigQuery
        bq_client = bigquery.Client()
        dataset_id = "corpchat"
        table_id = "embeddings"
        
        query = f"DELETE FROM `{bq_client.project}.{dataset_id}.{table_id}` WHERE 1=1"
        query_job = bq_client.query(query)
        query_job.result()
        
        # Limpiar metadata de Firestore
        firestore_client = firestore.Client()
        collection_name = "corpchat_attachments"
        
        # Eliminar todos los documentos
        docs = firestore_client.collection(collection_name).stream()
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
            
        _logger.info(f"Reset vector storage: BigQuery embeddings deleted, {deleted_count} Firestore docs deleted")
        
        return {
            "success": True,
            "message": "Vector storage and knowledge base reset",
            "bigquery_embeddings_deleted": True,
            "firestore_docs_deleted": deleted_count
        }
        
    except Exception as e:
        _logger.error(f"Error resetting vector storage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@app.post("/admin/reindex-knowledge-base")
async def reindex_knowledge_base():
    """Reindex knowledge base vectors (Danger Zone)"""
    try:
        from google.cloud import storage, bigquery, firestore
        
        # Obtener todos los documentos de Firestore
        firestore_client = firestore.Client()
        collection_name = "corpchat_attachments"
        
        docs = firestore_client.collection(collection_name).stream()
        reindexed_count = 0
        
        for doc in docs:
            doc_data = doc.to_dict()
            gcs_path = doc_data.get("gcs_path")
            
            if gcs_path:
                # Re-procesar documento
                from pipeline import IngestionPipeline
                pipeline = IngestionPipeline()
                
                await pipeline.process_file(
                    gcs_path=gcs_path,
                    attachment_id=doc.id,
                    chat_id=doc_data.get("chat_id", "reindex"),
                    user_id=doc_data.get("user_id", "system")
                )
                
                reindexed_count += 1
                
        _logger.info(f"Reindex knowledge base: {reindexed_count} documents reindexed")
        
        return {
            "success": True,
            "message": f"Knowledge base reindexed: {reindexed_count} documents processed",
            "reindexed_documents": reindexed_count
        }
        
    except Exception as e:
        _logger.error(f"Error reindexing knowledge base: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    
    _logger.info(f"🚀 Iniciando Ingestor en puerto {port}")
    _logger.info(f"📊 Pipeline: Extract → Chunk → Embed → Store (BigQuery)")
    
    uvicorn.run(app, host="0.0.0.0", port=port)

