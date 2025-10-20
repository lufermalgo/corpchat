"""
Servicio de Embeddings usando Vertex AI.

Genera embeddings de texto con text-embedding-004 (768 dimensiones).
Soporta generación individual y batch.
"""

import logging
from typing import List, Dict
from vertexai.language_models import TextEmbeddingModel

_logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Servicio para generar embeddings con Vertex AI.
    
    Usa text-embedding-004 que genera embeddings de 768 dimensiones
    optimizados para búsqueda semántica.
    """
    
    def __init__(self, model_name: str = "text-embedding-004"):
        """
        Inicializa el servicio de embeddings.
        
        Args:
            model_name: Nombre del modelo de embeddings
        """
        self.model_name = model_name
        self.model = None
        _logger.info(f"🧠 EmbeddingService configurado (modelo: {model_name})")
    
    def _get_model(self):
        """Lazy loading del modelo."""
        if self.model is None:
            _logger.info(f"📥 Cargando modelo {self.model_name}...")
            self.model = TextEmbeddingModel.from_pretrained(self.model_name)
            _logger.info(f"✅ Modelo cargado")
        return self.model
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Genera embedding de un texto.
        
        Args:
            text: Texto a embedizar
        
        Returns:
            Lista de 768 floats (embedding)
        
        Raises:
            ValueError: Si el texto está vacío
        """
        if not text or not text.strip():
            raise ValueError("Texto vacío no puede generar embedding")
        
        try:
            model = self._get_model()
            embeddings = model.get_embeddings([text])
            
            if not embeddings or not embeddings[0].values:
                raise ValueError("Modelo no retornó embedding")
            
            embedding = embeddings[0].values
            
            _logger.debug(
                f"✅ Embedding generado: {len(embedding)} dims, "
                f"texto: {len(text)} chars"
            )
            
            return embedding
        
        except Exception as e:
            _logger.error(f"❌ Error generando embedding: {e}", exc_info=True)
            raise
    
    def batch_generate(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Genera embeddings en batch.
        
        Vertex AI text-embedding-004 soporta hasta 250 textos por request.
        Este método procesa en batches para manejar listas grandes.
        
        Args:
            texts: Lista de textos
            batch_size: Tamaño de batch (max 250)
        
        Returns:
            Lista de embeddings (misma longitud que texts)
        """
        if not texts:
            return []
        
        # Validar batch_size
        if batch_size > 250:
            _logger.warning("⚠️ batch_size > 250, ajustando a 250")
            batch_size = 250
        
        try:
            model = self._get_model()
            all_embeddings = []
            
            # Procesar en batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                _logger.debug(
                    f"📊 Procesando batch {i//batch_size + 1}: "
                    f"{len(batch)} textos"
                )
                
                embeddings = model.get_embeddings(batch)
                
                batch_embeddings = [emb.values for emb in embeddings]
                all_embeddings.extend(batch_embeddings)
            
            _logger.info(
                f"✅ Batch embedding completado: {len(all_embeddings)} embeddings"
            )
            
            return all_embeddings
        
        except Exception as e:
            _logger.error(f"❌ Error en batch embedding: {e}", exc_info=True)
            raise
    
    def generate_for_chunks(
        self,
        chunks: List[Dict]
    ) -> List[Dict]:
        """
        Genera embeddings para una lista de chunks.
        
        Agrega el embedding a cada chunk en el campo "embedding".
        
        Args:
            chunks: Lista de chunks con campo "text"
        
        Returns:
            Chunks con campo "embedding" agregado
        """
        if not chunks:
            return []
        
        try:
            # Extraer textos
            texts = [chunk["text"] for chunk in chunks]
            
            _logger.info(f"🔄 Generando embeddings para {len(texts)} chunks...")
            
            # Generar embeddings en batch
            embeddings = self.batch_generate(texts)
            
            # Agregar embeddings a chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk["embedding"] = embedding
            
            _logger.info(f"✅ Embeddings agregados a {len(chunks)} chunks")
            
            return chunks
        
        except Exception as e:
            _logger.error(f"❌ Error generando embeddings para chunks: {e}")
            raise


if __name__ == "__main__":
    # Test básico
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Nota: Requiere configuración de GCP y Vertex AI
    try:
        service = EmbeddingService()
        
        # Test single embedding
        text = "Este es un texto de ejemplo para generar un embedding."
        embedding = service.generate_embedding(text)
        
        print(f"\n✅ Embedding generado:")
        print(f"   Dimensiones: {len(embedding)}")
        print(f"   Primeros 5 valores: {embedding[:5]}")
        
        # Test batch
        texts = [
            "Primer texto de ejemplo",
            "Segundo texto diferente",
            "Tercer texto para batch"
        ]
        
        embeddings = service.batch_generate(texts)
        print(f"\n✅ Batch embeddings generados: {len(embeddings)}")
        
    except Exception as e:
        print(f"\n❌ Error en test: {e}")
        print("\nNota: Requiere configuración de Vertex AI:")
        print("  export GOOGLE_CLOUD_PROJECT=$PROJECT_ID")
        print("  export GOOGLE_CLOUD_LOCATION=us-central1")

