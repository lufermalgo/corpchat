"""
ConfigManager para carga dinámica de configuración YAML.

Este módulo implementa el sistema de configuración del Core Cognitivo,
permitiendo carga dinámica de archivos YAML con validación usando Pydantic.
Sigue principios SOLID y DRY para máxima reutilización y mantenibilidad.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from pydantic import ValidationError

from ..shared.types import (
    CoreConfig, AgentConfig, ArgosCaseConfig, 
    ModelConfig, AgentSkill, ToolConfig
)
from ..shared.exceptions import ConfigurationError
from ..shared.utils import get_logger, validate_file_path, deep_merge_dicts


class ConfigManager:
    """
    Gestor de configuración para el Core Cognitivo.
    
    Maneja la carga, validación y acceso a configuraciones YAML
    de forma centralizada y eficiente.
    """
    
    def __init__(self, config_dir: Union[str, Path]):
        """
        Inicializa el ConfigManager.
        
        Args:
            config_dir: Directorio base de configuración
            
        Raises:
            ConfigurationError: Si el directorio no existe
        """
        self._logger = get_logger(__name__)
        self._config_dir = Path(config_dir)
        
        if not self._config_dir.exists():
            raise ConfigurationError(f"Directorio de configuración no existe: {config_dir}")
        
        self._config_cache: Dict[str, Any] = {}
        self._load_all_configs()
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Carga archivo YAML de forma segura.
        
        Args:
            file_path: Path al archivo YAML
            
        Returns:
            Diccionario con contenido del archivo
            
        Raises:
            ConfigurationError: Si hay error cargando el archivo
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = yaml.safe_load(file) or {}
                self._logger.debug(f"Archivo YAML cargado: {file_path}")
                return content
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parseando YAML {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error cargando archivo {file_path}: {e}")
    
    def _load_all_configs(self) -> None:
        """Carga todas las configuraciones disponibles."""
        try:
            # Cargar configuración principal
            core_config_path = self._config_dir / "core.yaml"
            if core_config_path.exists():
                self._config_cache["core"] = self._load_yaml_file(core_config_path)
            
            # Cargar configuraciones de agentes
            agents_dir = self._config_dir / "agents"
            if agents_dir.exists():
                self._config_cache["agents"] = {}
                for agent_file in agents_dir.glob("*.yaml"):
                    agent_name = agent_file.stem
                    self._config_cache["agents"][agent_name] = self._load_yaml_file(agent_file)
            
            # Cargar configuración de caso Argos
            argos_config_path = self._config_dir / "argos" / "argos_case.yaml"
            if argos_config_path.exists():
                self._config_cache["argos"] = self._load_yaml_file(argos_config_path)
            
            self._logger.info(f"Configuraciones cargadas desde: {self._config_dir}")
            
        except Exception as e:
            raise ConfigurationError(f"Error cargando configuraciones: {e}")
    
    def get_core_config(self) -> CoreConfig:
        """
        Obtiene configuración principal del core.
        
        Returns:
            Configuración principal validada
            
        Raises:
            ConfigurationError: Si la configuración no es válida
        """
        try:
            core_data = self._config_cache.get("core", {})
            return CoreConfig(**core_data)
        except ValidationError as e:
            raise ConfigurationError(f"Configuración core inválida: {e}")
    
    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """
        Obtiene configuración de agente específico.
        
        Args:
            agent_name: Nombre del agente
            
        Returns:
            Configuración del agente validada
            
        Raises:
            ConfigurationError: Si el agente no existe o configuración inválida
        """
        try:
            agents_data = self._config_cache.get("agents", {})
            if agent_name not in agents_data:
                raise ConfigurationError(f"Agente no encontrado: {agent_name}")
            
            agent_data = agents_data[agent_name]
            return AgentConfig(**agent_data)
        except ValidationError as e:
            raise ConfigurationError(f"Configuración de agente {agent_name} inválida: {e}")
    
    def get_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """
        Obtiene todas las configuraciones de agentes.
        
        Returns:
            Diccionario con configuraciones de agentes
        """
        agents_configs = {}
        agents_data = self._config_cache.get("agents", {})
        
        for agent_name, agent_data in agents_data.items():
            try:
                agents_configs[agent_name] = AgentConfig(**agent_data)
            except ValidationError as e:
                self._logger.warning(f"Configuración de agente {agent_name} inválida: {e}")
        
        return agents_configs
    
    def get_argos_case_config(self) -> ArgosCaseConfig:
        """
        Obtiene configuración del caso Argos.
        
        Returns:
            Configuración del caso Argos validada
            
        Raises:
            ConfigurationError: Si la configuración no es válida
        """
        try:
            argos_data = self._config_cache.get("argos", {})
            return ArgosCaseConfig(**argos_data)
        except ValidationError as e:
            raise ConfigurationError(f"Configuración del caso Argos inválida: {e}")
    
    def get_model_config(self, model_name: str) -> ModelConfig:
        """
        Obtiene configuración de modelo específico.
        
        Args:
            model_name: Nombre del modelo
            
        Returns:
            Configuración del modelo validada
            
        Raises:
            ConfigurationError: Si el modelo no existe
        """
        try:
            core_config = self.get_core_config()
            models = core_config.models
            
            if model_name not in models:
                raise ConfigurationError(f"Modelo no encontrado: {model_name}")
            
            return models[model_name]
        except Exception as e:
            raise ConfigurationError(f"Error obteniendo configuración de modelo {model_name}: {e}")
    
    def get_agent_skills(self, agent_name: str) -> List[AgentSkill]:
        """
        Obtiene skills de un agente específico.
        
        Args:
            agent_name: Nombre del agente
            
        Returns:
            Lista de skills del agente
        """
        try:
            agent_config = self.get_agent_config(agent_name)
            return agent_config.skills
        except Exception as e:
            self._logger.warning(f"Error obteniendo skills de agente {agent_name}: {e}")
            return []
    
    def get_agent_tools(self, agent_name: str) -> List[ToolConfig]:
        """
        Obtiene tools de un agente específico.
        
        Args:
            agent_name: Nombre del agente
            
        Returns:
            Lista de tools del agente
        """
        try:
            agent_config = self.get_agent_config(agent_name)
            return agent_config.tools
        except Exception as e:
            self._logger.warning(f"Error obteniendo tools de agente {agent_name}: {e}")
            return []
    
    def get_raw_config(self, section: str) -> Dict[str, Any]:
        """
        Obtiene configuración raw sin validación.
        
        Args:
            section: Sección de configuración
            
        Returns:
            Diccionario con configuración raw
        """
        return self._config_cache.get(section, {})
    
    def reload_config(self) -> None:
        """Recarga todas las configuraciones desde disco."""
        self._logger.info("Recargando configuraciones...")
        self._config_cache.clear()
        self._load_all_configs()
        self._logger.info("Configuraciones recargadas exitosamente")
    
    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combina dos configuraciones con override.
        
        Args:
            base_config: Configuración base
            override_config: Configuración de override
            
        Returns:
            Configuración combinada
        """
        return deep_merge_dicts(base_config, override_config)
    
    def validate_config(self) -> bool:
        """
        Valida todas las configuraciones cargadas.
        
        Returns:
            True si todas las configuraciones son válidas
            
        Raises:
            ConfigurationError: Si alguna configuración es inválida
        """
        try:
            # Validar configuración principal
            self.get_core_config()
            
            # Validar configuraciones de agentes
            self.get_all_agent_configs()
            
            # Validar configuración de caso Argos
            self.get_argos_case_config()
            
            self._logger.info("Todas las configuraciones son válidas")
            return True
            
        except Exception as e:
            raise ConfigurationError(f"Validación de configuración falló: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen de configuraciones cargadas.
        
        Returns:
            Diccionario con resumen de configuraciones
        """
        summary = {
            "config_dir": str(self._config_dir),
            "loaded_sections": list(self._config_cache.keys()),
            "agents_count": len(self._config_cache.get("agents", {})),
            "models_count": len(self.get_core_config().models),
        }
        
        return summary
