"""
BaseAgent abstracto para el Core Cognitivo.

Este módulo implementa la clase base abstracta para todos los agentes del sistema,
siguiendo principios SOLID y proporcionando funcionalidad común reutilizable.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from ..shared.types import AgentConfig, AgentSkill, ToolConfig, AgentType
from ..shared.exceptions import AgentError, ConfigurationError
from ..shared.utils import get_logger, measure_time
from ..config.config_manager import ConfigManager


class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes del Core Cognitivo.
    
    Implementa funcionalidad común y define la interfaz que deben
    implementar todos los agentes especializados.
    """
    
    def __init__(self, config: Union[AgentConfig, Dict[str, Any]], config_manager: Optional[ConfigManager] = None):
        """
        Inicializa el agente base.
        
        Args:
            config: Configuración del agente
            config_manager: Gestor de configuración (opcional)
            
        Raises:
            ConfigurationError: Si la configuración es inválida
        """
        self._logger = get_logger(self.__class__.__name__)
        
        # Convertir dict a AgentConfig si es necesario
        if isinstance(config, dict):
            try:
                self._config = AgentConfig(**config)
            except Exception as e:
                raise ConfigurationError(f"Configuración de agente inválida: {e}")
        else:
            self._config = config
        
        self._config_manager = config_manager
        self._skills: List[AgentSkill] = self._config.skills
        self._tools: List[ToolConfig] = self._config.tools
        self._enabled = self._config.enabled
        
        self._logger.info(f"Agente {self.name} inicializado")
    
    @property
    def name(self) -> str:
        """Nombre del agente."""
        return self._config.name
    
    @property
    def agent_type(self) -> AgentType:
        """Tipo del agente."""
        return self._config.type
    
    @property
    def model(self) -> str:
        """Modelo LLM del agente."""
        return self._config.model
    
    @property
    def enabled(self) -> bool:
        """Si el agente está habilitado."""
        return self._enabled
    
    @property
    def skills(self) -> List[AgentSkill]:
        """Skills del agente."""
        return self._skills
    
    @property
    def tools(self) -> List[ToolConfig]:
        """Tools del agente."""
        return self._tools
    
    @property
    def instruction(self) -> Optional[str]:
        """Instrucción específica del agente."""
        return self._config.instruction
    
    @property
    def sub_agents(self) -> Optional[List[str]]:
        """Sub-agentes del agente."""
        return self._config.sub_agents
    
    def get_skill_by_id(self, skill_id: str) -> Optional[AgentSkill]:
        """
        Obtiene skill por ID.
        
        Args:
            skill_id: ID del skill
            
        Returns:
            Skill encontrado o None
        """
        for skill in self._skills:
            if skill.id == skill_id:
                return skill
        return None
    
    def get_tool_by_name(self, tool_name: str) -> Optional[ToolConfig]:
        """
        Obtiene tool por nombre.
        
        Args:
            tool_name: Nombre del tool
            
        Returns:
            Tool encontrado o None
        """
        for tool in self._tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def has_skill(self, skill_id: str) -> bool:
        """
        Verifica si el agente tiene un skill específico.
        
        Args:
            skill_id: ID del skill
            
        Returns:
            True si tiene el skill
        """
        return self.get_skill_by_id(skill_id) is not None
    
    def has_tool(self, tool_name: str) -> bool:
        """
        Verifica si el agente tiene una herramienta específica.
        
        Args:
            tool_name: Nombre de la herramienta
            
        Returns:
            True si tiene la herramienta
        """
        return self.get_tool_by_name(tool_name) is not None
    
    def enable(self) -> None:
        """Habilita el agente."""
        self._enabled = True
        self._logger.info(f"Agente {self.name} habilitado")
    
    def disable(self) -> None:
        """Deshabilita el agente."""
        self._enabled = False
        self._logger.info(f"Agente {self.name} deshabilitado")
    
    def validate_skills(self) -> bool:
        """
        Valida que todos los skills sean válidos.
        
        Returns:
            True si todos los skills son válidos
            
        Raises:
            AgentError: Si algún skill es inválido
        """
        try:
            for skill in self._skills:
                if not skill.id:
                    raise AgentError(f"Skill sin ID en agente {self.name}")
                if not skill.name:
                    raise AgentError(f"Skill {skill.id} sin nombre en agente {self.name}")
                if not skill.description:
                    raise AgentError(f"Skill {skill.id} sin descripción en agente {self.name}")
            
            self._logger.debug(f"Skills del agente {self.name} validados exitosamente")
            return True
            
        except Exception as e:
            raise AgentError(f"Error validando skills del agente {self.name}: {e}")
    
    def validate_tools(self) -> bool:
        """
        Valida que todas las herramientas sean válidas.
        
        Returns:
            True si todas las herramientas son válidas
            
        Raises:
            AgentError: Si alguna herramienta es inválida
        """
        try:
            for tool in self._tools:
                if not tool.name:
                    raise AgentError(f"Tool sin nombre en agente {self.name}")
                if not tool.type:
                    raise AgentError(f"Tool {tool.name} sin tipo en agente {self.name}")
                if not tool.description:
                    raise AgentError(f"Tool {tool.name} sin descripción en agente {self.name}")
            
            self._logger.debug(f"Tools del agente {self.name} validados exitosamente")
            return True
            
        except Exception as e:
            raise AgentError(f"Error validando tools del agente {self.name}: {e}")
    
    def validate_configuration(self) -> bool:
        """
        Valida la configuración completa del agente.
        
        Returns:
            True si la configuración es válida
            
        Raises:
            AgentError: Si la configuración es inválida
        """
        try:
            # Validar configuración básica
            if not self.name:
                raise AgentError("Agente sin nombre")
            
            if not self.model:
                raise AgentError(f"Agente {self.name} sin modelo especificado")
            
            # Validar skills y tools
            self.validate_skills()
            self.validate_tools()
            
            self._logger.info(f"Configuración del agente {self.name} validada exitosamente")
            return True
            
        except Exception as e:
            raise AgentError(f"Error validando configuración del agente {self.name}: {e}")
    
    @abstractmethod
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa una consulta del usuario.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta del agente
            
        Raises:
            AgentError: Si hay error procesando la consulta
        """
        pass
    
    @abstractmethod
    def execute_skill(self, skill_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta un skill específico.
        
        Args:
            skill_id: ID del skill a ejecutar
            input_data: Datos de entrada
            
        Returns:
            Resultado de la ejecución
            
        Raises:
            AgentError: Si hay error ejecutando el skill
        """
        pass
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Obtiene información del agente.
        
        Returns:
            Diccionario con información del agente
        """
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "model": self.model,
            "enabled": self.enabled,
            "skills_count": len(self._skills),
            "tools_count": len(self._tools),
            "instruction": self.instruction,
            "sub_agents": self.sub_agents
        }
    
    def get_skills_info(self) -> List[Dict[str, Any]]:
        """
        Obtiene información de todos los skills.
        
        Returns:
            Lista con información de skills
        """
        return [
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "input_schema": skill.input_schema,
                "output_schema": skill.output_schema
            }
            for skill in self._skills
        ]
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """
        Obtiene información de todas las herramientas.
        
        Returns:
            Lista con información de herramientas
        """
        return [
            {
                "name": tool.name,
                "type": tool.type.value,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self._tools
        ]
    
    def __str__(self) -> str:
        """Representación string del agente."""
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"
    
    def __repr__(self) -> str:
        """Representación detallada del agente."""
        return (f"{self.__class__.__name__}("
                f"name='{self.name}', "
                f"type='{self.agent_type.value}', "
                f"model='{self.model}', "
                f"enabled={self.enabled}, "
                f"skills={len(self._skills)}, "
                f"tools={len(self._tools)})")
