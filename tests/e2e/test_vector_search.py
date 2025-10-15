#!/usr/bin/env python3
"""
Script para probar búsqueda semántica en los embeddings de BigQuery.

Uso:
    python test_vector_search.py "¿Qué es CorpChat?"
"""

import sys
import os
from google.cloud import bigquery
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import json

# Configuración
PROJECT_ID = "genai-385616"
REGION = "us-central1"
DATASET = "corpchat"
TABLE = "embeddings"

# Inicializar clientes
aiplatform.init(project=PROJECT_ID, location=REGION)
bq_client = bigquery.Client(project=PROJECT_ID)


def generate_embedding(text: str) -> list:
    """Genera embedding para un texto usando Vertex AI."""
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    embeddings = model.get_embeddings([text])
    return embeddings[0].values


def cosine_similarity_sql(query_embedding: list) -> str:
    """
    Genera la parte SQL para calcular cosine similarity.
    
    Cosine Similarity = (A · B) / (||A|| * ||B||)
    """
    # Convertir lista a string SQL
    embedding_str = ', '.join(str(v) for v in query_embedding)
    
    return f"""
    (
      -- Dot product (A · B)
      (SELECT SUM(a * b) 
       FROM UNNEST(embedding) AS a WITH OFFSET pos1
       JOIN UNNEST([{embedding_str}]) AS b WITH OFFSET pos2
       ON pos1 = pos2)
      /
      -- Magnitudes (||A|| * ||B||)
      (
        SQRT((SELECT SUM(a * a) FROM UNNEST(embedding) AS a))
        *
        SQRT((SELECT SUM(b * b) FROM UNNEST([{embedding_str}]) AS b))
      )
    )
    """


def search_similar_chunks(query_text: str, top_k: int = 5, min_score: float = 0.0):
    """
    Busca chunks similares al query usando vector search.
    
    Args:
        query_text: Texto de búsqueda
        top_k: Número de resultados a retornar
        min_score: Score mínimo de similitud (0-1)
    
    Returns:
        Lista de resultados con texto, score y metadata
    """
    print(f"\n🔍 Buscando: '{query_text}'")
    print(f"📊 Top {top_k} resultados con score >= {min_score}")
    print("=" * 80)
    
    # 1. Generar embedding del query
    print("\n[1/3] Generando embedding del query...")
    query_embedding = generate_embedding(query_text)
    print(f"✓ Embedding generado ({len(query_embedding)} dimensiones)")
    
    # 2. Construir query SQL con cosine similarity
    print("\n[2/3] Ejecutando búsqueda en BigQuery...")
    similarity_expr = cosine_similarity_sql(query_embedding)
    
    query = f"""
    SELECT 
      chunk_id,
      text,
      attachment_id,
      chat_id,
      user_id,
      chunk_index,
      page,
      source_filename,
      extraction_method,
      {similarity_expr} AS similarity_score,
      created_at
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
    WHERE {similarity_expr} >= {min_score}
    ORDER BY similarity_score DESC
    LIMIT {top_k}
    """
    
    # 3. Ejecutar query
    query_job = bq_client.query(query)
    results = list(query_job.result())
    
    print(f"✓ Encontrados {len(results)} resultados")
    
    # 4. Mostrar resultados
    print(f"\n[3/3] Resultados:")
    print("=" * 80)
    
    if not results:
        print("❌ No se encontraron resultados")
        return []
    
    output = []
    for i, row in enumerate(results, 1):
        result = {
            "rank": i,
            "similarity_score": float(row.similarity_score),
            "chunk_id": row.chunk_id,
            "text": row.text,
            "attachment_id": row.attachment_id,
            "user_id": row.user_id,
            "chunk_index": row.chunk_index,
            "page": row.page,
            "source_filename": row.source_filename,
            "extraction_method": row.extraction_method,
            "created_at": str(row.created_at)
        }
        output.append(result)
        
        # Imprimir resultado formateado
        print(f"\n#{i} - Score: {row.similarity_score:.4f}")
        print(f"Chunk ID: {row.chunk_id}")
        print(f"Attachment: {row.attachment_id}")
        print(f"Chunk {row.chunk_index} (Página: {row.page})")
        print(f"Método: {row.extraction_method}")
        print(f"Texto: {row.text[:200]}{'...' if len(row.text) > 200 else ''}")
        print("-" * 80)
    
    return output


def show_statistics():
    """Muestra estadísticas de los embeddings."""
    print("\n📊 Estadísticas de Embeddings")
    print("=" * 80)
    
    query = f"""
    SELECT 
      COUNT(*) as total,
      COUNT(DISTINCT user_id) as users,
      COUNT(DISTINCT attachment_id) as documents,
      MIN(created_at) as first,
      MAX(created_at) as last
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
    """
    
    result = list(bq_client.query(query).result())[0]
    
    print(f"Total embeddings: {result.total}")
    print(f"Usuarios únicos: {result.users}")
    print(f"Documentos únicos: {result.documents}")
    print(f"Primer embedding: {result.first}")
    print(f"Último embedding: {result.last}")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_vector_search.py <query>")
        print("\nEjemplos:")
        print("  python test_vector_search.py '¿Qué es CorpChat?'")
        print("  python test_vector_search.py 'RAG'")
        print("  python test_vector_search.py 'plataforma corporativa'")
        sys.exit(1)
    
    query_text = sys.argv[1]
    
    # Mostrar estadísticas
    show_statistics()
    
    # Ejecutar búsqueda
    results = search_similar_chunks(
        query_text=query_text,
        top_k=5,
        min_score=0.3  # Ajustar según necesidad
    )
    
    # Guardar resultados
    if results:
        output_file = f"/tmp/search_results_{os.getpid()}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Resultados guardados en: {output_file}")

