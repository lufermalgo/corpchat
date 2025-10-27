"""
Agent Manager - Gestor de Agentes con Google ADK.

Maneja el registro, descubrimiento y gestión de agentes
usando Google ADK como base.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from datetime import datetime

from google.adk.agents.llm_agent import Agent
from google.adk.tools import FunctionTool
from google.adk.workflows import SequentialAgent, ParallelAgent, LoopAgent

from ..a2a.agent_card import AgentCard
from ..shared.types import AgentConfig, ToolConfig, ProcessedData
from ..shared.exceptions import AgentError
from ..shared.utils import get_logger


class AgentFactory:
    """Factory para crear agentes usando Google ADK."""
    
    @staticmethod
    def create_agent(agent_config: AgentConfig) -> Agent:
        """
        Crea un agente usando Google ADK.
        
        Args:
            agent_config: Configuración del agente
            
        Returns:
            Agente de Google ADK
        """
        try:
            # Crear tools usando ADK
            tools = AgentFactory._create_tools(agent_config.tools)
            
            # Crear agente con ADK
            agent = Agent(
                model=agent_config.model,
                name=agent_config.name,
                instruction=agent_config.instruction,
                tools=tools
            )
            
            return agent
            
        except Exception as e:
            raise AgentError(f"Error creando agente {agent_config.name}: {e}")
    
    @staticmethod
    def _create_tools(tool_configs: List[ToolConfig]) -> List[FunctionTool]:
        """
        Crea tools usando Google ADK.
        
        Args:
            tool_configs: Configuraciones de tools
            
        Returns:
            Lista de FunctionTool de ADK
        """
        tools = []
        
        for tool_config in tool_configs:
            try:
                # Crear FunctionTool con ADK
                tool = FunctionTool(
                    name=tool_config.name,
                    description=tool_config.description,
                    func=tool_config.function
                )
                tools.append(tool)
                
            except Exception as e:
                logging.warning(f"Error creando tool {tool_config.name}: {e}")
                continue
        
        return tools


class AgentManager:
    """
    Gestor de agentes del Cognitive Core.
    
    Maneja el registro, descubrimiento y gestión de agentes
    usando Google ADK como base.
    """
    
    def __init__(self, config: Any):
        """
        Inicializa el Agent Manager.
        
        Args:
            config: Configuración del core
        """
        self.config = config
        self.logger = get_logger("AgentManager")
        
        # Registry de agentes
        self.agents: Dict[str, Agent] = {}
        self.agent_cards: Dict[str, AgentCard] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        
        self.logger.info("Agent Manager inicializado")
    
    async def register_agent(self, agent_config: AgentConfig) -> None:
        """
        Registra un agente en el manager.
        
        Args:
            agent_config: Configuración del agente
        """
        try:
            # Crear agente usando factory
            agent = AgentFactory.create_agent(agent_config)
            
            # Registrar en registry
            self.agents[agent_config.name] = agent
            self.agent_configs[agent_config.name] = agent_config
            
            # Crear Agent Card para A2A
            agent_card = self._create_agent_card(agent_config)
            self.agent_cards[agent_config.name] = agent_card
            
            self.logger.info(f"Agente registrado: {agent_config.name}")
            
        except Exception as e:
            self.logger.error(f"Error registrando agente {agent_config.name}: {e}")
            raise AgentError(f"Error registrando agente: {e}")
    
    async def unregister_agent(self, agent_name: str) -> None:
        """
        Desregistra un agente del manager.
        
        Args:
            agent_name: Nombre del agente
        """
        if agent_name in self.agents:
            del self.agents[agent_name]
            del self.agent_cards[agent_name]
            del self.agent_configs[agent_name]
            self.logger.info(f"Agente desregistrado: {agent_name}")
        else:
            self.logger.warning(f"Agente no encontrado: {agent_name}")
    
    async def discover_agents(self, processed_input: ProcessedData) -> List[Agent]:
        """
        Descubre agentes relevantes basado en el input procesado.
        
        Args:
            processed_input: Input procesado
            
        Returns:
            Lista de agentes relevantes
        """
        relevant_agents = []
        
        for agent_name, agent_card in self.agent_cards.items():
            if self._is_agent_relevant(agent_card, processed_input):
                relevant_agents.append(self.agents[agent_name])
        
        self.logger.info(f"Agentes descubiertos: {[agent.name for agent in relevant_agents]}")
        return relevant_agents
    
    def _is_agent_relevant(self, agent_card: AgentCard, processed_input: ProcessedData) -> bool:
        """
        Determina si un agente es relevante para el input.
        
        Args:
            agent_card: Tarjeta del agente
            processed_input: Input procesado
            
        Returns:
            True si el agente es relevante
        """
        # Lógica de matching basada en skills y contenido
        input_text = processed_input.get("text", "").lower()
        input_type = processed_input.get("type", "")
        
        # Verificar skills del agente
        for skill in agent_card.skills:
            skill_name = skill.get("name", "").lower()
            skill_keywords = skill.get("keywords", [])
            
            # Matching por nombre de skill
            if skill_name in input_text:
                return True
            
            # Matching por keywords
            for keyword in skill_keywords:
                if keyword.lower() in input_text:
                    return True
        
        # Matching por tipo de input
        if input_type in agent_card.metadata.get("supported_input_types", []):
            return True
        
        return False
    
    def _create_agent_card(self, agent_config: AgentConfig) -> AgentCard:
        """
        Crea una tarjeta de agente para A2A.
        
        Args:
            agent_config: Configuración del agente
            
        Returns:
            Tarjeta del agente
        """
        return AgentCard(
            id=agent_config.name,
            name=agent_config.name,
            description=agent_config.description,
            skills=agent_config.skills,
            endpoints={
                f"/{agent_config.name}": f"http://localhost:8000/agents/{agent_config.name}"
            },
            metadata={
                "model": agent_config.model,
                "tools": [tool.name for tool in agent_config.tools],
                "supported_input_types": agent_config.metadata.get("supported_input_types", ["text"]),
                "created_at": datetime.now().isoformat()
            }
        )
    
    def get_agent_cards(self) -> List[Dict[str, Any]]:
        """
        Retorna las tarjetas de agentes disponibles.
        
        Returns:
            Lista de tarjetas de agentes
        """
        return [card.to_dict() for card in self.agent_cards.values()]
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Retorna información de un agente específico.
        
        Args:
            agent_name: Nombre del agente
            
        Returns:
            Información del agente o None si no existe
        """
        if agent_name in self.agent_cards:
            return self.agent_cards[agent_name].to_dict()
        return None
    
    def list_agents(self) -> List[str]:
        """
        Retorna la lista de agentes registrados.
        
        Returns:
            Lista de nombres de agentes
        """
        return list(self.agents.keys())
    
    def get_agent_count(self) -> int:
        """
        Retorna el número de agentes registrados.
        
        Returns:
            Número de agentes
        """
        return len(self.agents)


def create_agent_manager(config: Any) -> AgentManager:
    """
    Crea una instancia del Agent Manager.
    
    Args:
        config: Configuración del core
        
    Returns:
        Instancia del Agent Manager
    """
    return AgentManager(config)
