"""
Tipos y modelos base para el Core Cognitivo.

Este módulo define los tipos fundamentales utilizados en toda la aplicación,
siguiendo principios SOLID y usando Pydantic para validación de datos.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class AgentType(str, Enum):
    """Tipos de agentes soportados por ADK."""
    LLM_AGENT = "LlmAgent"
    SEQUENTIAL_AGENT = "SequentialAgent"
    PARALLEL_AGENT = "ParallelAgent"
    LOOP_AGENT = "LoopAgent"


class ToolType(str, Enum):
    """Tipos de tools soportados por ADK."""
    FUNCTION_TOOL = "FunctionTool"
    WEB_SEARCH_TOOL = "WebSearchTool"
    CODE_EXECUTION_TOOL = "CodeExecutionTool"


class TaskStatus(str, Enum):
    """Estados de tareas según A2A Protocol."""
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    AUTH_REQUIRED = "auth-required"


class AuthenticationType(str, Enum):
    """Tipos de autenticación según A2A Protocol."""
    OAUTH = "oauth"
    API_KEY = "api_key"
    BASIC = "basic"
    NONE = "none"


class ModelConfig(BaseModel):
    """Configuración de modelos LLM."""
    display_name: str = Field(..., description="Nombre para mostrar del modelo")
    description: str = Field(..., description="Descripción del modelo")
    llm_model: str = Field(..., description="ID del modelo LLM")
    capabilities: List[str] = Field(default_factory=list, description="Capacidades del modelo")


class AgentSkill(BaseModel):
    """Definición de skill de agente según A2A Protocol."""
    id: str = Field(..., description="ID único del skill")
    name: str = Field(..., description="Nombre del skill")
    description: str = Field(..., description="Descripción del skill")
    input_schema: Dict[str, Any] = Field(..., description="Schema de entrada JSON")
    output_schema: Dict[str, Any] = Field(..., description="Schema de salida JSON")


class ToolConfig(BaseModel):
    """Configuración de herramienta."""
    name: str = Field(..., description="Nombre de la herramienta")
    type: ToolType = Field(..., description="Tipo de herramienta")
    description: str = Field(..., description="Descripción de la herramienta")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parámetros de configuración")


class AgentConfig(BaseModel):
    """Configuración de agente."""
    name: str = Field(..., description="Nombre del agente")
    type: AgentType = Field(..., description="Tipo de agente")
    model: str = Field(..., description="Modelo LLM a usar")
    enabled: bool = Field(True, description="Si el agente está habilitado")
    skills: List[AgentSkill] = Field(default_factory=list, description="Skills del agente")
    tools: List[ToolConfig] = Field(default_factory=list, description="Herramientas del agente")
    instruction: Optional[str] = Field(None, description="Instrucción específica del agente")
    sub_agents: Optional[List[str]] = Field(None, description="Sub-agentes")


class AuthenticationConfig(BaseModel):
    """Configuración de autenticación según A2A Protocol."""
    type: AuthenticationType = Field(..., description="Tipo de autenticación")
    authorization_endpoint: Optional[str] = Field(None, description="Endpoint de autorización")
    token_endpoint: Optional[str] = Field(None, description="Endpoint de token")
    scopes: Optional[List[str]] = Field(None, description="Scopes OAuth")


class AgentCard(BaseModel):
    """Agent Card según especificación A2A Protocol."""
    name: str = Field(..., description="Nombre del agente")
    version: str = Field("1.0.0", description="Versión del agente")
    description: str = Field(..., description="Descripción del agente")
    skills: List[AgentSkill] = Field(default_factory=list, description="Skills disponibles")
    authentication: Optional[AuthenticationConfig] = Field(None, description="Configuración de autenticación")
    endpoint: Optional[str] = Field(None, description="Endpoint del agente")


class TaskInfo(BaseModel):
    """Información de tarea según A2A Protocol."""
    task_id: str = Field(..., description="ID único de la tarea")
    context_id: str = Field(..., description="ID del contexto")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Estado de la tarea")
    skill_id: str = Field(..., description="ID del skill a ejecutar")
    input_data: Dict[str, Any] = Field(..., description="Datos de entrada")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Datos de salida")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falla")
    created_at: Optional[str] = Field(None, description="Timestamp de creación")
    updated_at: Optional[str] = Field(None, description="Timestamp de actualización")


class CoreConfig(BaseModel):
    """Configuración principal del Core Cognitivo."""
    core: Dict[str, Any] = Field(..., description="Configuración del core")
    models: Dict[str, ModelConfig] = Field(..., description="Modelos disponibles")
    orchestrator: Dict[str, Any] = Field(..., description="Configuración del orchestrator")
    session: Dict[str, Any] = Field(..., description="Configuración de sesión")
    a2a: Dict[str, Any] = Field(..., description="Configuración A2A Protocol")
    logging: Dict[str, Any] = Field(..., description="Configuración de logging")


class ArgosCaseConfig(BaseModel):
    """Configuración específica del caso Argos."""
    case: Dict[str, Any] = Field(..., description="Información del caso")
    scenario: Dict[str, Any] = Field(..., description="Escenario específico")
    validation: Dict[str, Any] = Field(..., description="Criterios de validación")
    test_data: Dict[str, Any] = Field(..., description="Datos de prueba")


class CognitiveCoreResponse(BaseModel):
    """Respuesta estándar del Core Cognitivo."""
    query: str = Field(..., description="Consulta original")
    analysis: Dict[str, Any] = Field(..., description="Análisis por agente")
    decision: Dict[str, Any] = Field(..., description="Decisión final integrada")
    confidence: float = Field(..., ge=0.0, le=100.0, description="Confianza de la respuesta")
    execution_time: Optional[float] = Field(None, description="Tiempo de ejecución en segundos")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
