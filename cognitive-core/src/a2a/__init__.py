"""
Implementación del Protocolo A2A (Agent2Agent).

Implementa los componentes base del protocolo A2A para comunicación
entre agentes heterogéneos.
"""

from .agent_executor import AgentExecutor
from .agent_card import AgentCard
from .request_context import RequestContext
from .event_queue import EventQueue
from .discovery import AgentDiscovery

__all__ = [
    "AgentExecutor",
    "AgentCard", 
    "RequestContext",
    "EventQueue",
    "AgentDiscovery"
]