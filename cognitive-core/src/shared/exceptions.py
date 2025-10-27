"""
Excepciones personalizadas para el Core Cognitivo.

Este módulo define excepciones específicas del dominio para manejo robusto de errores,
siguiendo principios SOLID y buenas prácticas de manejo de excepciones.
"""

from typing import Optional, Dict, Any


class CognitiveCoreException(Exception):
    """Excepción base para el Core Cognitivo."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ConfigurationError(CognitiveCoreException):
    """Error en configuración del sistema."""
    pass


class AgentError(CognitiveCoreException):
    """Error en ejecución de agente."""
    pass


class ToolError(CognitiveCoreException):
    """Error en ejecución de herramienta."""
    pass


class A2AProtocolError(CognitiveCoreException):
    """Error en protocolo A2A."""
    pass


class SessionError(CognitiveCoreException):
    """Error en gestión de sesión."""
    pass


class ValidationError(CognitiveCoreException):
    """Error de validación de datos."""
    pass


class OrchestrationError(CognitiveCoreException):
    """Error en orquestación de agentes."""
    pass


class ModelError(CognitiveCoreException):
    """Error en modelo LLM."""
    pass


class NetworkError(CognitiveCoreException):
    """Error de conectividad de red."""
    pass


class AuthenticationError(CognitiveCoreException):
    """Error de autenticación."""
    pass


class TimeoutError(CognitiveCoreException):
    """Error de timeout."""
    pass
