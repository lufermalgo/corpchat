"""Tool implementations following SOLID principles."""

from datetime import datetime
from typing import Dict, Any
from .interfaces import ITool, ToolResult


class TimeTool(ITool):
    """Time tool implementation (Single Responsibility Principle)."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @property
    def name(self) -> str:
        return self.config.get("name", "get_current_time")
    
    @property
    def description(self) -> str:
        return self.config.get("description", "Get the current date and time")
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute time tool."""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return ToolResult(success=True, result=current_time)
        except Exception as e:
            return ToolResult(success=False, result="", error=str(e))
    
    def is_enabled(self) -> bool:
        return self.config.get("enabled", True)


class MathTool(ITool):
    """Math tool implementation (Single Responsibility Principle)."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.allowed_chars = set(config.get("allowed_chars", "0123456789+-*/.() "))
    
    @property
    def name(self) -> str:
        return self.config.get("name", "calculate_math")
    
    @property
    def description(self) -> str:
        return self.config.get("description", "Safely evaluate mathematical expressions")
    
    def execute(self, expression: str = "", **kwargs) -> ToolResult:
        """Execute math tool."""
        try:
            if not expression:
                return ToolResult(success=False, result="", error="No expression provided")
            
            # Security check: only allow basic math operations
            if not all(c in self.allowed_chars for c in expression):
                return ToolResult(
                    success=False, 
                    result="", 
                    error="Only basic mathematical operations are allowed"
                )
            
            result = eval(expression)
            return ToolResult(success=True, result=f"Result: {result}")
            
        except Exception as e:
            return ToolResult(success=False, result="", error=f"Error calculating: {str(e)}")
    
    def is_enabled(self) -> bool:
        return self.config.get("enabled", True)


class InfoTool(ITool):
    """Info tool implementation (Single Responsibility Principle)."""
    
    def __init__(self, config: Dict[str, Any], agent_info: Dict[str, Any]):
        self.config = config
        self.agent_info = agent_info
    
    @property
    def name(self) -> str:
        return self.config.get("name", "get_agent_info")
    
    @property
    def description(self) -> str:
        return self.config.get("description", "Get information about the current agent")
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute info tool."""
        try:
            return ToolResult(success=True, result=str(self.agent_info))
        except Exception as e:
            return ToolResult(success=False, result="", error=str(e))
    
    def is_enabled(self) -> bool:
        return self.config.get("enabled", True)
