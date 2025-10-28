"""Base interfaces and abstract classes following SOLID principles."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    result: str
    error: Optional[str] = None


class ITool(ABC):
    """Interface for all tools (Interface Segregation Principle)."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if tool is enabled."""
        pass


class IAgentConfig(ABC):
    """Interface for agent configuration (Dependency Inversion Principle)."""
    
    @abstractmethod
    def get_agent_name(self) -> str:
        """Get agent name."""
        pass
    
    @abstractmethod
    def get_thinking_model_name(self) -> str:
        """Get thinking model name."""
        pass
    
    @abstractmethod
    def get_fast_model_name(self) -> str:
        """Get fast model name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get agent description."""
        pass
    
    @abstractmethod
    def get_thinking_generation_config(self) -> Dict[str, Any]:
        """Get thinking generation configuration."""
        pass
    
    @abstractmethod
    def get_fast_generation_config(self) -> Dict[str, Any]:
        """Get fast generation configuration."""
        pass
    
    @abstractmethod
    def get_thinking_config_for_planner(self) -> Dict[str, Any]:
        """Get thinking configuration for planner."""
        pass
    
    @abstractmethod
    def get_enabled_tools(self) -> List[str]:
        """Get enabled tools list."""
        pass
    
    @abstractmethod
    def get_instruction(self) -> str:
        """Get agent instruction."""
        pass
    
    @abstractmethod
    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration."""
        pass
    
    @abstractmethod
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        pass
    
    @abstractmethod
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """Get tool configuration."""
        pass
    
    @abstractmethod
    def is_thinking_enabled(self) -> bool:
        """Check if thinking is enabled."""
        pass


class IConfigLoader(ABC):
    """Interface for configuration loading (Dependency Inversion Principle)."""
    
    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        pass


class IToolFactory(ABC):
    """Interface for tool creation (Dependency Inversion Principle)."""
    
    @abstractmethod
    def create_tool(self, tool_name: str) -> ITool:
        pass
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        pass


class IAgentService(ABC):
    """Interface for agent operations (Interface Segregation Principle)."""
    
    @abstractmethod
    async def process_message(self, message: str, session_id: str, enable_thinking: Optional[bool] = None) -> Dict[str, Any]:
        """Process a message with optional thinking control."""
        pass
    
    @abstractmethod
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information."""
        pass
