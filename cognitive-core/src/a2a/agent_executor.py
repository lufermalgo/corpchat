"""
Agent Executor - Base para Agentes A2A.

Implementa la interfaz base para agentes que siguen el protocolo A2A.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from .request_context import RequestContext
from .event_queue import EventQueue
from ..shared.exceptions import A2AError
from ..shared.utils import get_logger


class AgentExecutor(ABC):
    """
    Clase base para agentes que implementan el protocolo A2A.
    
    Todos los agentes del sistema deben heredar de esta clase
    e implementar el método execute.
    """
    
    def __init__(self):
        """Inicializa el Agent Executor."""
        self.logger = get_logger(self.__class__.__name__)
        self.created_at = datetime.now()
        self.last_execution = None
        self.execution_count = 0
    
    @abstractmethod
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Ejecuta el agente con el contexto y cola de eventos proporcionados.
        
        Args:
            context: Contexto de la petición
            event_queue: Cola de eventos para comunicación
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del agente.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            "created_at": self.created_at.isoformat(),
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "execution_count": self.execution_count,
            "class_name": self.__class__.__name__
        }
    
    def _update_execution_stats(self):
        """Actualiza las estadísticas de ejecución."""
        self.last_execution = datetime.now()
        self.execution_count += 1
