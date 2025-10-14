"""
Firestore client para gestión de sesiones, chats y chunks.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

_logger = logging.getLogger(__name__)


class FirestoreClient:
    """Cliente de Firestore para operaciones de CorpChat."""
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Inicializa el cliente de Firestore.
        
        Args:
            project_id: ID del proyecto GCP (opcional, usa default)
        """
        self._db = firestore.Client(project=project_id) if project_id else firestore.Client()
        _logger.info("FirestoreClient inicializado")
    
    # ===== USUARIOS =====
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Diccionario con datos del usuario o None
        """
        doc_ref = self._db.collection('users').document(user_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    
    def create_or_update_user(self, user_id: str, data: Dict[str, Any]) -> None:
        """
        Crea o actualiza un usuario.
        
        Args:
            user_id: ID del usuario
            data: Datos del usuario
        """
        data['updated_at'] = datetime.now()
        self._db.collection('users').document(user_id).set(data, merge=True)
        _logger.info(f"Usuario actualizado: {user_id}")
    
    # ===== CHATS/SESIONES =====
    
    def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un chat.
        
        Args:
            chat_id: ID del chat
        
        Returns:
            Diccionario con datos del chat o None
        """
        doc_ref = self._db.collection('chats').document(chat_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    
    def create_chat(
        self,
        chat_id: str,
        owner_id: str,
        title: str = "Nuevo Chat",
        visibility: str = "private"
    ) -> None:
        """
        Crea un nuevo chat.
        
        Args:
            chat_id: ID del chat
            owner_id: ID del propietario
            title: Título del chat
            visibility: Visibilidad (private/team/org)
        """
        data = {
            'owner': owner_id,
            'title': title,
            'visibility': visibility,
            'members': [owner_id],
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'message_count': 0
        }
        self._db.collection('chats').document(chat_id).set(data)
        _logger.info(f"Chat creado: {chat_id} por {owner_id}")
    
    def update_chat(self, chat_id: str, data: Dict[str, Any]) -> None:
        """
        Actualiza un chat existente.
        
        Args:
            chat_id: ID del chat
            data: Datos a actualizar
        """
        data['updated_at'] = datetime.now()
        self._db.collection('chats').document(chat_id).set(data, merge=True)
    
    def get_user_chats(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene los chats de un usuario.
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de chats a retornar
        
        Returns:
            Lista de chats del usuario
        """
        chats_ref = self._db.collection('chats')
        query = chats_ref.where(
            filter=FieldFilter('members', 'array_contains', user_id)
        ).order_by('updated_at', direction=firestore.Query.DESCENDING).limit(limit)
        
        return [doc.to_dict() | {'id': doc.id} for doc in query.stream()]
    
    # ===== MENSAJES =====
    
    def add_message(
        self,
        chat_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Agrega un mensaje a un chat.
        
        Args:
            chat_id: ID del chat
            role: Rol (user/assistant/system)
            content: Contenido del mensaje
            metadata: Metadata adicional
        
        Returns:
            ID del mensaje creado
        """
        messages_ref = self._db.collection('chats').document(chat_id).collection('messages')
        
        message_data = {
            'role': role,
            'content': content,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        }
        
        doc_ref = messages_ref.add(message_data)[1]
        
        # Incrementar contador de mensajes
        self._db.collection('chats').document(chat_id).update({
            'message_count': firestore.Increment(1),
            'updated_at': datetime.now()
        })
        
        return doc_ref.id
    
    def get_chat_history(
        self,
        chat_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de mensajes de un chat.
        
        Args:
            chat_id: ID del chat
            limit: Número máximo de mensajes
        
        Returns:
            Lista de mensajes ordenados por timestamp descendente
        """
        messages_ref = self._db.collection('chats').document(chat_id).collection('messages')
        query = messages_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        
        messages = [doc.to_dict() | {'id': doc.id} for doc in query.stream()]
        return list(reversed(messages))  # Retornar en orden cronológico
    
    # ===== ADJUNTOS =====
    
    def create_attachment(
        self,
        attachment_id: str,
        user_id: str,
        chat_id: str,
        gcs_path: str,
        filename: str,
        mime_type: str,
        size_bytes: int
    ) -> None:
        """
        Registra un adjunto.
        
        Args:
            attachment_id: ID del adjunto
            user_id: ID del usuario que subió
            chat_id: ID del chat asociado
            gcs_path: Ruta en GCS
            filename: Nombre del archivo
            mime_type: Tipo MIME
            size_bytes: Tamaño en bytes
        """
        data = {
            'user_id': user_id,
            'chat_id': chat_id,
            'gcs_path': gcs_path,
            'filename': filename,
            'mime_type': mime_type,
            'size_bytes': size_bytes,
            'status': 'processing',
            'uploaded_at': datetime.now(),
            'processed_at': None,
            'error': None
        }
        self._db.collection('attachments').document(attachment_id).set(data)
        _logger.info(f"Adjunto registrado: {attachment_id}")
    
    def update_attachment_status(
        self,
        attachment_id: str,
        status: str,
        error: Optional[str] = None
    ) -> None:
        """
        Actualiza el estado de un adjunto.
        
        Args:
            attachment_id: ID del adjunto
            status: Nuevo estado (processing/ready/failed)
            error: Mensaje de error si aplica
        """
        data = {
            'status': status,
            'processed_at': datetime.now() if status in ['ready', 'failed'] else None
        }
        if error:
            data['error'] = error
        
        self._db.collection('attachments').document(attachment_id).update(data)
        _logger.info(f"Adjunto {attachment_id} → {status}")
    
    def get_attachment(self, attachment_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un adjunto.
        
        Args:
            attachment_id: ID del adjunto
        
        Returns:
            Diccionario con datos del adjunto o None
        """
        doc_ref = self._db.collection('attachments').document(attachment_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    
    def get_chat_attachments(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene los adjuntos de un chat.
        
        Args:
            chat_id: ID del chat
        
        Returns:
            Lista de adjuntos
        """
        attachments_ref = self._db.collection('attachments')
        query = attachments_ref.where(
            filter=FieldFilter('chat_id', '==', chat_id)
        ).order_by('uploaded_at', direction=firestore.Query.DESCENDING)
        
        return [doc.to_dict() | {'id': doc.id} for doc in query.stream()]
    
    # ===== CHUNKS Y EMBEDDINGS =====
    
    def add_chunk(
        self,
        chat_id: str,
        chunk_id: str,
        attachment_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Agrega un chunk con su embedding.
        
        Args:
            chat_id: ID del chat
            chunk_id: ID del chunk
            attachment_id: ID del adjunto fuente
            text: Texto del chunk
            embedding: Vector de embedding
            metadata: Metadata (page, coords, method, confidence, etc.)
        """
        chunk_data = {
            'attachment_id': attachment_id,
            'text': text,
            'embedding': embedding,
            'metadata': metadata,
            'created_at': datetime.now()
        }
        
        self._db.collection('chats').document(chat_id).collection('chunks').document(chunk_id).set(chunk_data)
        _logger.debug(f"Chunk {chunk_id} agregado al chat {chat_id}")
    
    def search_chunks(
        self,
        chat_id: str,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca chunks similares usando embeddings.
        
        Nota: Firestore no soporta búsqueda vectorial nativa.
        Para MVP, retorna todos los chunks y filtra en memoria.
        En producción, migrar a Vertex AI Vector Search.
        
        Args:
            chat_id: ID del chat
            query_embedding: Embedding de la query
            limit: Número máximo de resultados
            threshold: Umbral de similitud
        
        Returns:
            Lista de chunks ordenados por similitud
        """
        chunks_ref = self._db.collection('chats').document(chat_id).collection('chunks')
        all_chunks = [doc.to_dict() | {'id': doc.id} for doc in chunks_ref.stream()]
        
        # Calcular similitud coseno
        def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            return dot_product / (norm1 * norm2) if norm1 and norm2 else 0.0
        
        # Calcular similitud para cada chunk
        for chunk in all_chunks:
            chunk['similarity'] = cosine_similarity(query_embedding, chunk['embedding'])
        
        # Filtrar por threshold y ordenar
        filtered_chunks = [c for c in all_chunks if c['similarity'] >= threshold]
        filtered_chunks.sort(key=lambda x: x['similarity'], reverse=True)
        
        return filtered_chunks[:limit]
    
    def delete_chat_chunks(self, chat_id: str) -> int:
        """
        Elimina todos los chunks de un chat.
        
        Args:
            chat_id: ID del chat
        
        Returns:
            Número de chunks eliminados
        """
        chunks_ref = self._db.collection('chats').document(chat_id).collection('chunks')
        deleted_count = 0
        
        # Eliminar en batches
        batch = self._db.batch()
        for doc in chunks_ref.stream():
            batch.delete(doc.reference)
            deleted_count += 1
            
            if deleted_count % 500 == 0:  # Commit cada 500 docs
                batch.commit()
                batch = self._db.batch()
        
        batch.commit()
        _logger.info(f"Eliminados {deleted_count} chunks del chat {chat_id}")
        return deleted_count
    
    # ===== KNOWLEDGE BASE =====
    
    def add_to_kb(
        self,
        kb_domain: str,
        content_id: str,
        title: str,
        content: str,
        source: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Agrega contenido a una Knowledge Base por dominio.
        
        Args:
            kb_domain: Dominio de KB (empresa/tecnico/productos)
            content_id: ID del contenido
            title: Título
            content: Contenido
            source: Fuente (chatId, userId, etc.)
            metadata: Metadata adicional
        """
        data = {
            'title': title,
            'content': content,
            'source': source,
            'metadata': metadata,
            'created_at': datetime.now(),
            'version': 1
        }
        
        self._db.collection('knowledge_base').document(kb_domain).collection('contents').document(content_id).set(data)
        _logger.info(f"Contenido {content_id} agregado a KB {kb_domain}")
    
    def search_kb(
        self,
        kb_domain: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Busca en la Knowledge Base.
        
        Nota: Implementación básica con búsqueda de texto.
        En producción, usar embeddings + vector search.
        
        Args:
            kb_domain: Dominio de KB
            query: Query de búsqueda
            limit: Número máximo de resultados
        
        Returns:
            Lista de contenidos relevantes
        """
        kb_ref = self._db.collection('knowledge_base').document(kb_domain).collection('contents')
        
        # Por ahora, retornar los más recientes
        # TODO: Implementar búsqueda vectorial
        query_ref = kb_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
        
        return [doc.to_dict() | {'id': doc.id} for doc in query_ref.stream()]

