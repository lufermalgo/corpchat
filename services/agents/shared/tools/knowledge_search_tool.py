"""
ADK Tool para búsqueda en Knowledge Base usando BigQuery Vector Search.

Este tool permite a los agentes buscar información en la base de conocimiento
corporativa usando búsqueda semántica con embeddings.
"""

import logging
from typing import List, Optional
from vertexai.language_models import TextEmbeddingModel

# Importar BigQueryVectorSearch desde shared
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from bigquery_vector_search import BigQueryVectorSearch

_logger = logging.getLogger(__name__)


def search_knowledge_base(
    query: str,
    top_k: int = 5,
    chat_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> str:
    """
    Busca en la base de conocimiento corporativa usando búsqueda semántica.
    
    Esta función genera un embedding de la query y busca los chunks
    de documentos más similares en BigQuery usando cosine similarity.
    
    Args:
        query: Pregunta o texto a buscar
        top_k: Número de resultados a retornar (default 5)
        chat_id: ID del chat para filtrar búsqueda (opcional)
        user_id: ID del usuario para filtrar búsqueda (opcional)
    
    Returns:
        String formateado con los resultados más relevantes, incluyendo:
        - Texto del chunk
        - Fuente (documento, página)
        - Score de similaridad
    
    Example:
        >>> results = search_knowledge_base("política de vacaciones")
        >>> print(results)
        "1. [Score: 0.89] Fuente: politicas_rrhh.pdf (pág. 5)
         Las vacaciones anuales son de 15 días hábiles..."
    """
    try:
        _logger.info(f"🔍 Buscando en KB: '{query[:50]}...' (top_k={top_k})")
        
        # 1. Generar embedding de la query
        embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        embeddings = embedding_model.get_embeddings([query])
        query_embedding = embeddings[0].values
        
        _logger.debug(f"✅ Embedding generado: {len(query_embedding)} dimensiones")
        
        # 2. Buscar en BigQuery
        bq_search = BigQueryVectorSearch()
        results = bq_search.search_similar_chunks(
            query_embedding=query_embedding,
            chat_id=chat_id,
            user_id=user_id,
            top_k=top_k,
            similarity_threshold=0.7
        )
        
        # 3. Formatear resultados
        if not results:
            return "No se encontraron resultados relevantes en la base de conocimiento."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            score = result.get('similarity', 0.0)
            text = result.get('text', '')
            source = result.get('source_filename', 'Desconocido')
            page = result.get('page')
            
            page_info = f" (pág. {page})" if page else ""
            formatted_results.append(
                f"{i}. [Score: {score:.2f}] Fuente: {source}{page_info}\n   {text[:200]}..."
            )
        
        result_text = "\n\n".join(formatted_results)
        _logger.info(f"✅ {len(results)} resultados encontrados")
        
        return f"Resultados de búsqueda en base de conocimiento:\n\n{result_text}"
    
    except Exception as e:
        _logger.error(f"❌ Error en búsqueda KB: {e}", exc_info=True)
        return f"Error al buscar en la base de conocimiento: {str(e)}"


# Para registrar como ADK Tool, necesitamos que sea una función simple
# ADK detecta automáticamente funciones con docstrings apropiados
__all__ = ["search_knowledge_base"]

