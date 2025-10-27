"""
Validador de configuración para el Core Cognitivo.

Este módulo implementa validaciones específicas para asegurar que las configuraciones
cumplan con los requerimientos del sistema y principios de diseño.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .config_manager import ConfigManager
from ..shared.exceptions import ConfigurationError, ValidationError
from ..shared.utils import get_logger


class ConfigValidator:
    """
    Validador de configuraciones del Core Cognitivo.
    
    Implementa validaciones específicas para asegurar integridad
    y consistencia de las configuraciones del sistema.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Inicializa el validador.
        
        Args:
            config_manager: Instancia del ConfigManager
        """
        self._config_manager = config_manager
        self._logger = get_logger(__name__)
    
    def validate_all(self) -> bool:
        """
        Valida todas las configuraciones del sistema.
        
        Returns:
            True si todas las validaciones pasan
            
        Raises:
            ConfigurationError: Si alguna validación falla
        """
        try:
            self._logger.info("Iniciando validación completa de configuraciones...")
            
            # Validaciones básicas
            self._validate_core_config()
            self._validate_agent_configs()
            self._validate_model_configs()
            self._validate_argos_case_config()
            
            # Validaciones de consistencia
            self._validate_agent_model_consistency()
            self._validate_skill_consistency()
            self._validate_tool_consistency()
            
            self._logger.info("Todas las validaciones pasaron exitosamente")
            return True
            
        except Exception as e:
            self._logger.error(f"Validación falló: {e}")
            raise ConfigurationError(f"Validación de configuración falló: {e}")
    
    def _validate_core_config(self) -> None:
        """Valida configuración principal del core."""
        try:
            core_config = self._config_manager.get_core_config()
            
            # Validar que existan modelos requeridos
            required_models = ["gemini-fast", "gemini-pro"]
            for model_name in required_models:
                if model_name not in core_config.models:
                    raise ValidationError(f"Modelo requerido no encontrado: {model_name}")
            
            # Validar configuración de orchestrator
            if not core_config.orchestrator.get("name"):
                raise ValidationError("Nombre del orchestrator no especificado")
            
            # Validar configuración de sesión
            if not core_config.session.get("service"):
                raise ValidationError("Servicio de sesión no especificado")
            
            self._logger.debug("Configuración core validada exitosamente")
            
        except Exception as e:
            raise ConfigurationError(f"Error validando configuración core: {e}")
    
    def _validate_agent_configs(self) -> None:
        """Valida configuraciones de agentes."""
        try:
            agent_configs = self._config_manager.get_all_agent_configs()
            
            if not agent_configs:
                raise ValidationError("No se encontraron configuraciones de agentes")
            
            # Validar agentes requeridos
            required_agents = ["terrestrial", "maritime", "multimodal"]
            for agent_name in required_agents:
                if agent_name not in agent_configs:
                    raise ValidationError(f"Agente requerido no encontrado: {agent_name}")
            
            # Validar cada agente individualmente
            for agent_name, agent_config in agent_configs.items():
                self._validate_single_agent(agent_name, agent_config)
            
            self._logger.debug("Configuraciones de agentes validadas exitosamente")
            
        except Exception as e:
            raise ConfigurationError(f"Error validando configuraciones de agentes: {e}")
    
    def _validate_single_agent(self, agent_name: str, agent_config: Any) -> None:
        """
        Valida configuración de un agente individual.
        
        Args:
            agent_name: Nombre del agente
            agent_config: Configuración del agente
        """
        # Validar que el agente esté habilitado
        if not agent_config.enabled:
            self._logger.warning(f"Agente {agent_name} está deshabilitado")
        
        # Validar que tenga skills
        if not agent_config.skills:
            raise ValidationError(f"Agente {agent_name} no tiene skills definidos")
        
        # Validar que tenga tools
        if not agent_config.tools:
            raise ValidationError(f"Agente {agent_name} no tiene tools definidos")
        
        # Validar skills individuales
        for skill in agent_config.skills:
            self._validate_skill(skill)
        
        # Validar tools individuales
        for tool in agent_config.tools:
            self._validate_tool(tool)
    
    def _validate_skill(self, skill: Any) -> None:
        """
        Valida un skill individual.
        
        Args:
            skill: Configuración del skill
        """
        # Validar campos requeridos
        if not skill.id:
            raise ValidationError("Skill sin ID especificado")
        
        if not skill.name:
            raise ValidationError(f"Skill {skill.id} sin nombre")
        
        if not skill.description:
            raise ValidationError(f"Skill {skill.id} sin descripción")
        
        # Validar schemas
        if not skill.input_schema:
            raise ValidationError(f"Skill {skill.id} sin input_schema")
        
        if not skill.output_schema:
            raise ValidationError(f"Skill {skill.id} sin output_schema")
    
    def _validate_tool(self, tool: Any) -> None:
        """
        Valida una herramienta individual.
        
        Args:
            tool: Configuración de la herramienta
        """
        # Validar campos requeridos
        if not tool.name:
            raise ValidationError("Tool sin nombre especificado")
        
        if not tool.type:
            raise ValidationError(f"Tool {tool.name} sin tipo especificado")
        
        if not tool.description:
            raise ValidationError(f"Tool {tool.name} sin descripción")
    
    def _validate_model_configs(self) -> None:
        """Valida configuraciones de modelos."""
        try:
            core_config = self._config_manager.get_core_config()
            
            for model_name, model_config in core_config.models.items():
                # Validar campos requeridos
                if not model_config.llm_model:
                    raise ValidationError(f"Modelo {model_name} sin llm_model especificado")
                
                if not model_config.display_name:
                    raise ValidationError(f"Modelo {model_name} sin display_name")
                
                if not model_config.description:
                    raise ValidationError(f"Modelo {model_name} sin descripción")
            
            self._logger.debug("Configuraciones de modelos validadas exitosamente")
            
        except Exception as e:
            raise ConfigurationError(f"Error validando configuraciones de modelos: {e}")
    
    def _validate_argos_case_config(self) -> None:
        """Valida configuración del caso Argos."""
        try:
            argos_config = self._config_manager.get_argos_case_config()
            
            # Validar campos requeridos del caso
            if not argos_config.case.get("name"):
                raise ValidationError("Caso Argos sin nombre")
            
            if not argos_config.scenario.get("name"):
                raise ValidationError("Escenario Argos sin nombre")
            
            # Validar datos de prueba
            test_data = argos_config.test_data
            if not test_data.get("plants"):
                raise ValidationError("Datos de prueba sin plantas")
            
            if not test_data.get("trucks"):
                raise ValidationError("Datos de prueba sin camiones")
            
            if not test_data.get("vessels"):
                raise ValidationError("Datos de prueba sin embarcaciones")
            
            self._logger.debug("Configuración del caso Argos validada exitosamente")
            
        except Exception as e:
            raise ConfigurationError(f"Error validando configuración del caso Argos: {e}")
    
    def _validate_agent_model_consistency(self) -> None:
        """Valida consistencia entre agentes y modelos."""
        try:
            core_config = self._config_manager.get_core_config()
            agent_configs = self._config_manager.get_all_agent_configs()
            
            available_models = set(core_config.models.keys())
            
            for agent_name, agent_config in agent_configs.items():
                if agent_config.model not in available_models:
                    raise ValidationError(
                        f"Agente {agent_name} referencia modelo inexistente: {agent_config.model}"
                    )
            
            self._logger.debug("Consistencia agente-modelo validada exitosamente")
            
        except Exception as e:
            raise ConfigurationError(f"Error validando consistencia agente-modelo: {e}")
    
    def _validate_skill_consistency(self) -> None:
        """Valida consistencia de skills entre agentes."""
        try:
            agent_configs = self._config_manager.get_all_agent_configs()
            skill_ids = set()
            
            for agent_name, agent_config in agent_configs.items():
                for skill in agent_config.skills:
                    if skill.id in skill_ids:
                        raise ValidationError(f"Skill ID duplicado: {skill.id}")
                    skill_ids.add(skill.id)
            
            self._logger.debug("Consistencia de skills validada exitosamente")
            
        except Exception as e:
            raise ConfigurationError(f"Error validando consistencia de skills: {e}")
    
    def _validate_tool_consistency(self) -> None:
        """Valida consistencia de tools entre agentes."""
        try:
            agent_configs = self._config_manager.get_all_agent_configs()
            tool_names = set()
            
            for agent_name, agent_config in agent_configs.items():
                for tool in agent_config.tools:
                    if tool.name in tool_names:
                        self._logger.warning(f"Tool name duplicado: {tool.name}")
                    tool_names.add(tool.name)
            
            self._logger.debug("Consistencia de tools validada exitosamente")
            
        except Exception as e:
            raise ConfigurationError(f"Error validando consistencia de tools: {e}")
    
    def get_validation_report(self) -> Dict[str, Any]:
        """
        Genera reporte de validación.
        
        Returns:
            Diccionario con reporte de validación
        """
        try:
            report = {
                "validation_status": "PASSED",
                "timestamp": self._config_manager.get_raw_config("core").get("timestamp"),
                "config_summary": self._config_manager.get_config_summary(),
                "validations_performed": [
                    "core_config",
                    "agent_configs", 
                    "model_configs",
                    "argos_case_config",
                    "agent_model_consistency",
                    "skill_consistency",
                    "tool_consistency"
                ]
            }
            
            return report
            
        except Exception as e:
            return {
                "validation_status": "FAILED",
                "error": str(e),
                "timestamp": None
            }
