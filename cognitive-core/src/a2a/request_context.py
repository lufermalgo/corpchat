"""
Request Context - Contexto de Petición A2A.

Maneja el contexto de peticiones en el protocolo A2A.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

from ..shared.utils import get_logger


@dataclass
class RequestContext:
    """
    Contexto de petición para el protocolo A2A.
    
    Contiene toda la información necesaria para procesar una petición
    en el sistema multi-agente.
    """
    
    # Información básica de la petición
    message: str
    request_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Metadatos de la petición
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Información del usuario/cliente
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Configuración de procesamiento
    processing_options: Dict[str, Any] = field(default_factory=dict)
    
    # Historial de la conversación
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Contexto compartido entre agentes
    shared_context: Dict[str, Any] = field(default_factory=dict)
    
    def add_to_conversation(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Agrega un mensaje al historial de conversación.
        
        Args:
            role: Rol del emisor (user, agent, system)
            content: Contenido del mensaje
            metadata: Metadatos adicionales
        """
        message_entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message_entry)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Retorna un resumen de la conversación.
        
        Returns:
            Resumen de la conversación
        """
        return {
            "message_count": len(self.conversation_history),
            "last_message": self.conversation_history[-1] if self.conversation_history else None,
            "participants": list(set(msg["role"] for msg in self.conversation_history)),
            "duration": (datetime.now() - self.timestamp).total_seconds()
        }
    
    def update_shared_context(self, key: str, value: Any):
        """
        Actualiza el contexto compartido.
        
        Args:
            key: Clave del contexto
            value: Valor a almacenar
        """
        self.shared_context[key] = value
    
    def get_shared_context(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor del contexto compartido.
        
        Args:
            key: Clave del contexto
            default: Valor por defecto
            
        Returns:
            Valor del contexto o valor por defecto
        """
        return self.shared_context.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el contexto a diccionario.
        
        Returns:
            Diccionario con el contexto
        """
        return {
            "message": self.message,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "processing_options": self.processing_options,
            "conversation_history": self.conversation_history,
            "shared_context": self.shared_context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequestContext":
        """
        Crea un RequestContext desde un diccionario.
        
        Args:
            data: Datos del contexto
            
        Returns:
            Instancia de RequestContext
        """
        return cls(
            message=data["message"],
            request_id=data["request_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            processing_options=data.get("processing_options", {}),
            conversation_history=data.get("conversation_history", []),
            shared_context=data.get("shared_context", {})
        )


def create_request_context(
    message: str,
    request_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> RequestContext:
    """
    Crea un RequestContext con los parámetros proporcionados.
    
    Args:
        message: Mensaje de la petición
        request_id: ID único de la petición
        user_id: ID del usuario
        session_id: ID de la sesión
        metadata: Metadatos adicionales
        
    Returns:
        Instancia de RequestContext
    """
    return RequestContext(
        message=message,
        request_id=request_id,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata or {}
    )
