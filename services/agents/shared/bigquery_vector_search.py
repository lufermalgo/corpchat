"""
BigQuery Vector Search para CorpChat.

Implementa búsqueda semántica usando BigQuery ML.DISTANCE para cosine similarity.
Los embeddings se almacenan en BigQuery para búsquedas escalables y cost-effective.

Uso:
    from shared.bigquery_vector_search import BigQueryVectorSearch
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
    bq_search = BigQueryVectorSearch(project_id=project_id)
    results = bq_search.search_similar_chunks(
        query_embedding=query_vector,
        chat_id="chat_abc123",
        top_k=5
    )
"""

from google.cloud import bigquery
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import os

_logger = logging.getLogger(__name__)


class BigQueryVectorSearch:
    """
    Cliente de búsqueda vectorial usando BigQuery.
    
    Gestiona operaciones de insert y search sobre la tabla de embeddings.
    """
    
    def __init__(
        self, 
        project_id: str = None,
        dataset: str = "corpchat",
        table: str = "embeddings"
    ):
        """
        Inicializa el cliente de BigQuery para vector search.
        
        Args:
            project_id: ID del proyecto GCP
            dataset: Nombre del dataset BigQuery
            table: Nombre de la tabla de embeddings
        """
        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
        
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset = dataset
        self.table = table
        self.table_ref = f"{project_id}.{dataset}.{table}"
        
        _logger.info(f"BigQueryVectorSearch inicializado: {self.table_ref}")
    
    def search_similar_chunks(
        self,
        query_embedding: List[float],
        chat_id: Optional[str] = None,
        user_id: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda de chunks similares usando cosine similarity.
        
        Args:
            query_embedding: Vector de embedding de la query (768 dims para text-embedding-004)
            chat_id: ID del chat para filtrar (None para búsqueda global)
            user_id: ID del usuario para filtrar (None para todos)
            top_k: Número máximo de resultados
            similarity_threshold: Umbral mínimo de similaridad (0-1)
            include_expired: Si True, incluye chunks expirados
        
        Returns:
            Lista de chunks ordenados por similaridad descendente
        """
        # Validar dimensión del embedding
        if len(query_embedding) != 768:
            _logger.warning(f"Embedding dimension {len(query_embedding)} != 768 esperados")
        
        # Convertir embedding a formato BigQuery array
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # Construir query SQL dinámicamente
        where_clauses = []
        query_params = []
        
        if chat_id:
            where_clauses.append("chat_id = @chat_id")
            query_params.append(
                bigquery.ScalarQueryParameter("chat_id", "STRING", chat_id)
            )
        
        if user_id:
            where_clauses.append("user_id = @user_id")
            query_params.append(
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
            )
        
        if not include_expired:
            where_clauses.append("(expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP())")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Query SQL con ML.DISTANCE
        query = f"""
        WITH query_embedding AS (
          SELECT {embedding_str} as embedding
        )
        SELECT 
          chunk_id,
          text,
          page,
          source_filename,
          extraction_method,
          attachment_id,
          chat_id,
          user_id,
          chunk_index,
          created_at,
          -- Calcular similaridad (1 - cosine distance = cosine similarity)
          1 - ML.DISTANCE(
            t.embedding, 
            q.embedding, 
            'COSINE'
          ) as similarity
        FROM 
          `{self.table_ref}` t,
          query_embedding q
        WHERE 
          {where_clause}
        HAVING 
          similarity >= @threshold
        ORDER BY 
          similarity DESC
        LIMIT @top_k
        """
        
        query_params.extend([
            bigquery.ScalarQueryParameter("threshold", "FLOAT64", similarity_threshold),
            bigquery.ScalarQueryParameter("top_k", "INT64", top_k),
        ])
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        
        try:
            _logger.debug(f"Ejecutando vector search: chat_id={chat_id}, top_k={top_k}")
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            chunks = []
            for row in results:
                chunks.append({
                    'chunk_id': row.chunk_id,
                    'text': row.text,
                    'page': row.page,
                    'source_filename': row.source_filename,
                    'extraction_method': row.extraction_method,
                    'attachment_id': row.attachment_id,
                    'chat_id': row.chat_id,
                    'user_id': row.user_id,
                    'chunk_index': row.chunk_index,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'similarity': float(row.similarity)
                })
            
            _logger.info(
                f"Vector search completado: {len(chunks)} chunks encontrados "
                f"(chat_id={chat_id}, threshold={similarity_threshold})"
            )
            return chunks
            
        except Exception as e:
            _logger.error(f"Error en búsqueda vectorial: {e}", exc_info=True)
            return []
    
    def insert_chunks(
        self, 
        chunks: List[Dict[str, Any]],
        ttl_days: Optional[int] = None
    ) -> bool:
        """
        Insertar chunks con embeddings en BigQuery.
        
        Args:
            chunks: Lista de dicts con estructura:
                {
                    'chunk_id': str,
                    'attachment_id': str,
                    'chat_id': str,
                    'user_id': str,
                    'text': str,
                    'embedding': List[float],  # 768 dims
                    'page': Optional[int],
                    'source_filename': Optional[str],
                    'chunk_index': Optional[int],
                    'extraction_method': Optional[str]
                }
            ttl_days: Días hasta expiración (None = sin expiración)
        
        Returns:
            True si la inserción fue exitosa
        """
        if not chunks:
            _logger.warning("insert_chunks llamado sin chunks")
            return True
        
        # Agregar timestamps y expires_at
        now = datetime.utcnow()
        expires_at = (now + timedelta(days=ttl_days)) if ttl_days else None
        
        rows_to_insert = []
        for chunk in chunks:
            # Validar campos requeridos
            required_fields = ['chunk_id', 'attachment_id', 'chat_id', 'user_id', 'text', 'embedding']
            missing_fields = [f for f in required_fields if f not in chunk]
            if missing_fields:
                _logger.error(f"Chunk falta campos requeridos: {missing_fields}")
                continue
            
            # Validar dimensión del embedding
            if len(chunk['embedding']) != 768:
                _logger.error(f"Chunk {chunk['chunk_id']}: embedding dimension {len(chunk['embedding'])} != 768")
                continue
            
            row = {
                'chunk_id': chunk['chunk_id'],
                'attachment_id': chunk['attachment_id'],
                'chat_id': chunk['chat_id'],
                'user_id': chunk['user_id'],
                'text': chunk['text'],
                'embedding': chunk['embedding'],
                'page': chunk.get('page'),
                'source_filename': chunk.get('source_filename'),
                'chunk_index': chunk.get('chunk_index'),
                'extraction_method': chunk.get('extraction_method'),
                'created_at': now.isoformat(),
                'expires_at': expires_at.isoformat() if expires_at else None
            }
            rows_to_insert.append(row)
        
        if not rows_to_insert:
            _logger.error("No hay chunks válidos para insertar")
            return False
        
        try:
            # Insertar en BigQuery
            errors = self.client.insert_rows_json(self.table_ref, rows_to_insert)
            
            if errors:
                _logger.error(f"Errores al insertar en BigQuery: {errors}")
                return False
            
            _logger.info(
                f"Insertados {len(rows_to_insert)} chunks en BigQuery "
                f"(ttl_days={ttl_days})"
            )
            return True
            
        except Exception as e:
            _logger.error(f"Error al insertar chunks en BigQuery: {e}", exc_info=True)
            return False
    
    def delete_chunks_by_chat(self, chat_id: str) -> bool:
        """
        Eliminar todos los chunks de un chat.
        
        Args:
            chat_id: ID del chat
        
        Returns:
            True si la eliminación fue exitosa
        """
        query = f"""
        DELETE FROM `{self.table_ref}`
        WHERE chat_id = @chat_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("chat_id", "STRING", chat_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()  # Wait for completion
            
            _logger.info(f"Eliminados chunks del chat: {chat_id}")
            return True
            
        except Exception as e:
            _logger.error(f"Error al eliminar chunks del chat {chat_id}: {e}", exc_info=True)
            return False
    
    def delete_chunks_by_attachment(self, attachment_id: str) -> bool:
        """
        Eliminar todos los chunks de un attachment.
        
        Args:
            attachment_id: ID del attachment
        
        Returns:
            True si la eliminación fue exitosa
        """
        query = f"""
        DELETE FROM `{self.table_ref}`
        WHERE attachment_id = @attachment_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("attachment_id", "STRING", attachment_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
            _logger.info(f"Eliminados chunks del attachment: {attachment_id}")
            return True
            
        except Exception as e:
            _logger.error(f"Error al eliminar chunks del attachment {attachment_id}: {e}", exc_info=True)
            return False
    
    def get_stats(self, chat_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener estadísticas de la tabla de embeddings.
        
        Args:
            chat_id: Si se proporciona, estadísticas solo para ese chat
        
        Returns:
            Dict con estadísticas: total_chunks, storage_bytes, etc.
        """
        where_clause = f"WHERE chat_id = '{chat_id}'" if chat_id else ""
        
        query = f"""
        SELECT 
          COUNT(*) as total_chunks,
          COUNT(DISTINCT chat_id) as total_chats,
          COUNT(DISTINCT user_id) as total_users,
          COUNT(DISTINCT attachment_id) as total_attachments,
          AVG(ARRAY_LENGTH(embedding)) as avg_embedding_dims
        FROM `{self.table_ref}`
        {where_clause}
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            row = list(results)[0]
            stats = {
                'total_chunks': int(row.total_chunks),
                'total_chats': int(row.total_chats),
                'total_users': int(row.total_users),
                'total_attachments': int(row.total_attachments),
                'avg_embedding_dims': float(row.avg_embedding_dims) if row.avg_embedding_dims else 0
            }
            
            _logger.info(f"Stats obtenidas: {stats}")
            return stats
            
        except Exception as e:
            _logger.error(f"Error al obtener stats: {e}", exc_info=True)
            return {
                'total_chunks': 0,
                'total_chats': 0,
                'total_users': 0,
                'total_attachments': 0,
                'avg_embedding_dims': 0
            }

