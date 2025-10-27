"""
Event Queue - Cola de Eventos A2A.

Maneja la comunicación asíncrona entre agentes usando colas de eventos.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque

from ..shared.exceptions import A2AError
from ..shared.utils import get_logger


@dataclass
class Event:
    """
    Evento en la cola A2A.
    
    Representa un evento de comunicación entre agentes.
    """
    
    # Información básica del evento
    event_id: str
    event_type: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Metadatos del evento
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Información del emisor y receptor
    sender_id: Optional[str] = None
    receiver_id: Optional[str] = None
    
    # Prioridad del evento
    priority: int = 0  # 0 = normal, 1 = high, -1 = low
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el evento a diccionario.
        
        Returns:
            Diccionario con el evento
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "priority": self.priority
        }


class EventQueue:
    """
    Cola de eventos para comunicación A2A.
    
    Maneja la comunicación asíncrona entre agentes usando
    una cola de eventos con prioridades.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Inicializa la cola de eventos.
        
        Args:
            max_size: Tamaño máximo de la cola
        """
        self.max_size = max_size
        self.logger = get_logger("EventQueue")
        
        # Colas por prioridad
        self.high_priority_queue = deque()
        self.normal_priority_queue = deque()
        self.low_priority_queue = deque()
        
        # Estadísticas
        self.total_events_processed = 0
        self.total_events_dropped = 0
        
        # Lock para operaciones thread-safe
        self._lock = asyncio.Lock()
        
        self.logger.info(f"Event Queue inicializada con tamaño máximo: {max_size}")
    
    async def put(self, event_data: Dict[str, Any], priority: int = 0) -> None:
        """
        Agrega un evento a la cola.
        
        Args:
            event_data: Datos del evento
            priority: Prioridad del evento (1=high, 0=normal, -1=low)
        """
        async with self._lock:
            # Verificar si la cola está llena
            if self._get_total_size() >= self.max_size:
                self.total_events_dropped += 1
                self.logger.warning("Cola de eventos llena, descartando evento")
                return
            
            # Crear evento
            event = Event(
                event_id=event_data.get("event_id", f"event_{datetime.now().timestamp()}"),
                event_type=event_data.get("type", "message"),
                content=event_data.get("content"),
                metadata=event_data.get("metadata", {}),
                sender_id=event_data.get("sender_id"),
                receiver_id=event_data.get("receiver_id"),
                priority=priority
            )
            
            # Agregar a la cola apropiada
            if priority > 0:
                self.high_priority_queue.append(event)
            elif priority < 0:
                self.low_priority_queue.append(event)
            else:
                self.normal_priority_queue.append(event)
            
            self.logger.debug(f"Evento agregado a la cola: {event.event_id}")
    
    async def get(self, timeout: Optional[float] = None) -> Optional[Event]:
        """
        Obtiene el siguiente evento de la cola.
        
        Args:
            timeout: Timeout en segundos
            
        Returns:
            Evento o None si no hay eventos
        """
        async with self._lock:
            # Buscar evento por prioridad
            event = None
            
            if self.high_priority_queue:
                event = self.high_priority_queue.popleft()
            elif self.normal_priority_queue:
                event = self.normal_priority_queue.popleft()
            elif self.low_priority_queue:
                event = self.low_priority_queue.popleft()
            
            if event:
                self.total_events_processed += 1
                self.logger.debug(f"Evento procesado: {event.event_id}")
                return event
            
            return None
    
    async def peek(self) -> Optional[Event]:
        """
        Observa el siguiente evento sin removerlo de la cola.
        
        Returns:
            Evento o None si no hay eventos
        """
        async with self._lock:
            if self.high_priority_queue:
                return self.high_priority_queue[0]
            elif self.normal_priority_queue:
                return self.normal_priority_queue[0]
            elif self.low_priority_queue:
                return self.low_priority_queue[0]
            
            return None
    
    def _get_total_size(self) -> int:
        """
        Retorna el tamaño total de todas las colas.
        
        Returns:
            Tamaño total
        """
        return (
            len(self.high_priority_queue) +
            len(self.normal_priority_queue) +
            len(self.low_priority_queue)
        )
    
    def size(self) -> int:
        """
        Retorna el tamaño actual de la cola.
        
        Returns:
            Tamaño actual
        """
        return self._get_total_size()
    
    def is_empty(self) -> bool:
        """
        Verifica si la cola está vacía.
        
        Returns:
            True si está vacía
        """
        return self._get_total_size() == 0
    
    def is_full(self) -> bool:
        """
        Verifica si la cola está llena.
        
        Returns:
            True si está llena
        """
        return self._get_total_size() >= self.max_size
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de la cola.
        
        Returns:
            Estadísticas de la cola
        """
        return {
            "total_size": self._get_total_size(),
            "high_priority_size": len(self.high_priority_queue),
            "normal_priority_size": len(self.normal_priority_queue),
            "low_priority_size": len(self.low_priority_queue),
            "max_size": self.max_size,
            "total_events_processed": self.total_events_processed,
            "total_events_dropped": self.total_events_dropped,
            "is_empty": self.is_empty(),
            "is_full": self.is_full()
        }
    
    async def clear(self) -> None:
        """
        Limpia todas las colas.
        """
        async with self._lock:
            self.high_priority_queue.clear()
            self.normal_priority_queue.clear()
            self.low_priority_queue.clear()
            self.logger.info("Cola de eventos limpiada")
    
    async def get_events_by_type(self, event_type: str) -> List[Event]:
        """
        Obtiene todos los eventos de un tipo específico.
        
        Args:
            event_type: Tipo de evento
            
        Returns:
            Lista de eventos del tipo especificado
        """
        async with self._lock:
            events = []
            
            # Buscar en todas las colas
            for queue in [self.high_priority_queue, self.normal_priority_queue, self.low_priority_queue]:
                for event in queue:
                    if event.event_type == event_type:
                        events.append(event)
            
            return events


def create_event_queue(max_size: int = 1000) -> EventQueue:
    """
    Crea una instancia de EventQueue.
    
    Args:
        max_size: Tamaño máximo de la cola
        
    Returns:
        Instancia de EventQueue
    """
    return EventQueue(max_size)
