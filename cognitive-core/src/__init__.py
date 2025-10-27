"""
Core Cognitivo - Sistema Multi-Agente Genérico.

Este paquete implementa un sistema de agentes cognitivos genérico
basado en Google ADK y protocolo A2A.
"""

from .core import (
    CognitiveCore,
    AgentManager,
    PipelineProcessor,
    Orchestrator,
    KnowledgeSynthesizer,
    DecisionEngine
)

from .a2a import (
    AgentExecutor,
    AgentCard,
    RequestContext,
    EventQueue,
    AgentDiscovery
)

from .shared import (
    CoreConfig,
    AgentConfig,
    ToolConfig,
    ProcessedData,
    CoreError,
    AgentError,
    A2AError,
    get_logger
)

__version__ = "1.0.0"
__author__ = "CorpChat Development Team"
__description__ = "Core Cognitivo - Sistema Multi-Agente Genérico"

__all__ = [
    # Core
    "CognitiveCore",
    "AgentManager",
    "PipelineProcessor",
    "Orchestrator",
    "KnowledgeSynthesizer",
    "DecisionEngine",
    
    # A2A
    "AgentExecutor",
    "AgentCard",
    "RequestContext",
    "EventQueue",
    "AgentDiscovery",
    
    # Shared
    "CoreConfig",
    "AgentConfig",
    "ToolConfig",
    "ProcessedData",
    "CoreError",
    "AgentError",
    "A2AError",
    "get_logger",
    
    # Metadata
    "__version__",
    "__author__",
    "__description__"
]