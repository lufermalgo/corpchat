"""Tool factory implementation following SOLID principles."""

from typing import Dict, Any, List
from .interfaces import IToolFactory, ITool
from .tools import TimeTool, MathTool, InfoTool


class ToolFactory(IToolFactory):
    """Tool factory implementation (Open/Closed Principle)."""
    
    def __init__(self, agent_config, agent_info: Dict[str, Any]):
        self.agent_config = agent_config
        self.agent_info = agent_info
        self._tool_registry = {
            "time_tool": self._create_time_tool,
            "math_tool": self._create_math_tool,
            "info_tool": self._create_info_tool,
        }
    
    def create_tool(self, tool_name: str) -> ITool:
        """Create a tool by name."""
        if tool_name not in self._tool_registry:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return self._tool_registry[tool_name]()
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self._tool_registry.keys())
    
    def create_all_enabled_tools(self) -> List[ITool]:
        """Create all enabled tools."""
        enabled_tools = []
        enabled_tool_names = self.agent_config.get_enabled_tools()
        
        for tool_name in enabled_tool_names:
            if tool_name in self._tool_registry:
                try:
                    tool = self.create_tool(tool_name)
                    if tool.is_enabled():
                        enabled_tools.append(tool)
                except Exception as e:
                    print(f"Warning: Failed to create tool {tool_name}: {e}")
        
        return enabled_tools
    
    def _create_time_tool(self) -> ITool:
        """Create time tool."""
        config = self.agent_config.get_tool_config("time_tool")
        return TimeTool(config)
    
    def _create_math_tool(self) -> ITool:
        """Create math tool."""
        config = self.agent_config.get_tool_config("math_tool")
        return MathTool(config)
    
    def _create_info_tool(self) -> ITool:
        """Create info tool."""
        config = self.agent_config.get_tool_config("info_tool")
        return InfoTool(config, self.agent_info)
