"""
Agent Discovery - Descubrimiento de Agentes A2A.

Implementa el descubrimiento dinámico de agentes usando el protocolo A2A.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .agent_card import AgentCard
from .request_context import RequestContext
from ..shared.exceptions import A2AError
from ..shared.utils import get_logger


class AgentDiscovery:
    """
    Servicio de descubrimiento de agentes A2A.
    
    Permite descubrir agentes disponibles en el sistema
    y mantener un registro actualizado.
    """
    
    def __init__(self):
        """Inicializa el servicio de descubrimiento."""
        self.logger = get_logger("AgentDiscovery")
        self.agent_registry: Dict[str, AgentCard] = {}
        self.discovery_cache: Dict[str, datetime] = {}
        self.cache_ttl_seconds = 300  # 5 minutos
        
        self.logger.info("Agent Discovery inicializado")
    
    async def register_agent(self, agent_card: AgentCard) -> None:
        """
        Registra un agente en el sistema de descubrimiento.
        
        Args:
            agent_card: Tarjeta del agente
        """
        self.agent_registry[agent_card.id] = agent_card
        self.discovery_cache[agent_card.id] = datetime.now()
        
        self.logger.info(f"Agente registrado: {agent_card.name}")
    
    async def unregister_agent(self, agent_id: str) -> None:
        """
        Desregistra un agente del sistema.
        
        Args:
            agent_id: ID del agente
        """
        if agent_id in self.agent_registry:
            del self.agent_registry[agent_id]
            del self.discovery_cache[agent_id]
            self.logger.info(f"Agente desregistrado: {agent_id}")
    
    async def discover_agents(self, query: Optional[Dict[str, Any]] = None) -> List[AgentCard]:
        """
        Descubre agentes basado en una consulta.
        
        Args:
            query: Consulta de descubrimiento
            
        Returns:
            Lista de agentes que coinciden con la consulta
        """
        matching_agents = []
        
        for agent_card in self.agent_registry.values():
            if self._matches_query(agent_card, query):
                matching_agents.append(agent_card)
        
        self.logger.info(f"Agentes descubiertos: {len(matching_agents)}")
        return matching_agents
    
    def _matches_query(self, agent_card: AgentCard, query: Optional[Dict[str, Any]]) -> bool:
        """
        Verifica si un agente coincide con la consulta.
        
        Args:
            agent_card: Tarjeta del agente
            query: Consulta
            
        Returns:
            True si coincide
        """
        if not query:
            return True
        
        # Matching por skills
        if "skills" in query:
            required_skills = query["skills"]
            agent_skills = [skill["name"] for skill in agent_card.skills]
            
            if not all(skill in agent_skills for skill in required_skills):
                return False
        
        # Matching por metadata
        if "metadata" in query:
            required_metadata = query["metadata"]
            for key, value in required_metadata.items():
                if agent_card.metadata.get(key) != value:
                    return False
        
        return True
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentCard]:
        """
        Obtiene un agente por su ID.
        
        Args:
            agent_id: ID del agente
            
        Returns:
            Tarjeta del agente o None si no existe
        """
        return self.agent_registry.get(agent_id)
    
    async def list_all_agents(self) -> List[AgentCard]:
        """
        Lista todos los agentes registrados.
        
        Returns:
            Lista de todos los agentes
        """
        return list(self.agent_registry.values())
    
    async def cleanup_expired_agents(self) -> None:
        """
        Limpia agentes expirados del cache.
        """
        current_time = datetime.now()
        expired_agents = []
        
        for agent_id, last_seen in self.discovery_cache.items():
            if (current_time - last_seen).total_seconds() > self.cache_ttl_seconds:
                expired_agents.append(agent_id)
        
        for agent_id in expired_agents:
            await self.unregister_agent(agent_id)
        
        if expired_agents:
            self.logger.info(f"Agentes expirados limpiados: {len(expired_agents)}")
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del registro.
        
        Returns:
            Estadísticas del registro
        """
        return {
            "total_agents": len(self.agent_registry),
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "last_cleanup": datetime.now().isoformat()
        }


def create_agent_discovery() -> AgentDiscovery:
    """
    Crea una instancia del servicio de descubrimiento.
    
    Returns:
        Instancia de AgentDiscovery
    """
    return AgentDiscovery()
