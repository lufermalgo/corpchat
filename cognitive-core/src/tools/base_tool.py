"""
BaseTool abstracto para el Core Cognitivo.

Este módulo implementa la clase base abstracta para todas las herramientas del sistema,
siguiendo principios SOLID y proporcionando funcionalidad común reutilizable.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, Callable
from pathlib import Path

from ..shared.types import ToolConfig, ToolType
from ..shared.exceptions import ToolError, ConfigurationError
from ..shared.utils import get_logger, measure_time


class BaseTool(ABC):
    """
    Clase base abstracta para todas las herramientas del Core Cognitivo.
    
    Implementa funcionalidad común y define la interfaz que deben
    implementar todas las herramientas especializadas.
    """
    
    def __init__(self, config: Union[ToolConfig, Dict[str, Any]]):
        """
        Inicializa la herramienta base.
        
        Args:
            config: Configuración de la herramienta
            
        Raises:
            ConfigurationError: Si la configuración es inválida
        """
        self._logger = get_logger(self.__class__.__name__)
        
        # Convertir dict a ToolConfig si es necesario
        if isinstance(config, dict):
            try:
                self._config = ToolConfig(**config)
            except Exception as e:
                raise ConfigurationError(f"Configuración de herramienta inválida: {e}")
        else:
            self._config = config
        
        self._name = self._config.name
        self._tool_type = self._config.type
        self._description = self._config.description
        self._parameters = self._config.parameters or {}
        
        self._logger.info(f"Herramienta {self.name} inicializada")
    
    @property
    def name(self) -> str:
        """Nombre de la herramienta."""
        return self._name
    
    @property
    def tool_type(self) -> ToolType:
        """Tipo de la herramienta."""
        return self._tool_type
    
    @property
    def description(self) -> str:
        """Descripción de la herramienta."""
        return self._description
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Parámetros de configuración de la herramienta."""
        return self._parameters
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un parámetro de configuración.
        
        Args:
            key: Clave del parámetro
            default: Valor por defecto
            
        Returns:
            Valor del parámetro o valor por defecto
        """
        return self._parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """
        Establece un parámetro de configuración.
        
        Args:
            key: Clave del parámetro
            value: Valor del parámetro
        """
        self._parameters[key] = value
        self._logger.debug(f"Parámetro {key} establecido en herramienta {self.name}")
    
    def validate_parameters(self) -> bool:
        """
        Valida los parámetros de configuración.
        
        Returns:
            True si los parámetros son válidos
            
        Raises:
            ToolError: Si los parámetros son inválidos
        """
        try:
            # Validación básica - puede ser extendida por subclases
            if not self._name:
                raise ToolError("Herramienta sin nombre")
            
            if not self._description:
                raise ToolError(f"Herramienta {self._name} sin descripción")
            
            self._logger.debug(f"Parámetros de herramienta {self.name} validados exitosamente")
            return True
            
        except Exception as e:
            raise ToolError(f"Error validando parámetros de herramienta {self.name}: {e}")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Valida datos de entrada para la herramienta.
        
        Args:
            input_data: Datos de entrada a validar
            
        Returns:
            True si los datos son válidos
            
        Raises:
            ToolError: Si los datos son inválidos
        """
        try:
            # Validación básica - puede ser extendida por subclases
            if not isinstance(input_data, dict):
                raise ToolError("Datos de entrada deben ser un diccionario")
            
            self._logger.debug(f"Datos de entrada validados para herramienta {self.name}")
            return True
            
        except Exception as e:
            raise ToolError(f"Error validando datos de entrada para herramienta {self.name}: {e}")
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta la herramienta con los datos de entrada proporcionados.
        
        Args:
            input_data: Datos de entrada para la herramienta
            context: Contexto adicional (opcional)
            
        Returns:
            Resultado de la ejecución
            
        Raises:
            ToolError: Si hay error ejecutando la herramienta
        """
        pass
    
    @measure_time
    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta la herramienta con validación y manejo de errores.
        
        Args:
            input_data: Datos de entrada para la herramienta
            context: Contexto adicional (opcional)
            
        Returns:
            Resultado de la ejecución
            
        Raises:
            ToolError: Si hay error ejecutando la herramienta
        """
        try:
            # Validar parámetros
            self.validate_parameters()
            
            # Validar datos de entrada
            self.validate_input(input_data)
            
            # Ejecutar herramienta
            result = self.execute(input_data, context)
            
            self._logger.info(f"Herramienta {self.name} ejecutada exitosamente")
            return result
            
        except Exception as e:
            self._logger.error(f"Error ejecutando herramienta {self.name}: {e}")
            raise ToolError(f"Error ejecutando herramienta {self.name}: {e}")
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        Obtiene información de la herramienta.
        
        Returns:
            Diccionario con información de la herramienta
        """
        return {
            "name": self.name,
            "type": self.tool_type.value,
            "description": self.description,
            "parameters": self.parameters
        }
    
    def __str__(self) -> str:
        """Representación string de la herramienta."""
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.tool_type.value}')"
    
    def __repr__(self) -> str:
        """Representación detallada de la herramienta."""
        return (f"{self.__class__.__name__}("
                f"name='{self.name}', "
                f"type='{self.tool_type.value}', "
                f"description='{self.description}')")


class FunctionTool(BaseTool):
    """
    Implementación de FunctionTool para herramientas basadas en funciones.
    
    Esta clase permite crear herramientas a partir de funciones Python,
    siguiendo el patrón de Google ADK FunctionTool.
    """
    
    def __init__(self, func: Callable, config: Union[ToolConfig, Dict[str, Any]]):
        """
        Inicializa FunctionTool con una función Python.
        
        Args:
            func: Función Python a ejecutar
            config: Configuración de la herramienta
            
        Raises:
            ConfigurationError: Si la función o configuración es inválida
        """
        super().__init__(config)
        
        if not callable(func):
            raise ConfigurationError(f"Función no es callable para herramienta {self.name}")
        
        self._func = func
        self._logger.info(f"FunctionTool {self.name} inicializada con función {func.__name__}")
    
    def execute(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta la función con los datos de entrada.
        
        Args:
            input_data: Datos de entrada para la función
            context: Contexto adicional (opcional)
            
        Returns:
            Resultado de la ejecución de la función
            
        Raises:
            ToolError: Si hay error ejecutando la función
        """
        try:
            # Preparar argumentos para la función
            if context is not None:
                # Si la función acepta context como parámetro
                import inspect
                sig = inspect.signature(self._func)
                if 'context' in sig.parameters:
                    result = self._func(**input_data, context=context)
                else:
                    result = self._func(**input_data)
            else:
                result = self._func(**input_data)
            
            # Convertir resultado a diccionario si es necesario
            if not isinstance(result, dict):
                result = {"result": result}
            
            return result
            
        except Exception as e:
            raise ToolError(f"Error ejecutando función {self._func.__name__}: {e}")
    
    def get_function_info(self) -> Dict[str, Any]:
        """
        Obtiene información de la función asociada.
        
        Returns:
            Diccionario con información de la función
        """
        import inspect
        
        return {
            "function_name": self._func.__name__,
            "function_doc": self._func.__doc__,
            "function_signature": str(inspect.signature(self._func)),
            "tool_info": self.get_tool_info()
        }
