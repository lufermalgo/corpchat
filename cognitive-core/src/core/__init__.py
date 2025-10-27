"""
Core genérico del Cognitive Core.

Este paquete contiene los componentes centrales del sistema multi-agente
basado en Google ADK y protocolo A2A.
"""

from .cognitive_core import CognitiveCore
from .agent_manager import AgentManager
from .pipeline_processor import PipelineProcessor
from .orchestrator import Orchestrator
from .knowledge_synthesizer import KnowledgeSynthesizer
from .decision_engine import DecisionEngine

__all__ = [
    "CognitiveCore",
    "AgentManager", 
    "PipelineProcessor",
    "Orchestrator",
    "KnowledgeSynthesizer",
    "DecisionEngine"
]