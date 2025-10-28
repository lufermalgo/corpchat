"""Agent configuration implementation."""

import logging
from typing import Dict, Any, List
from google.genai import types
from google.genai.types import ThinkingConfig
from google.adk.planners import BuiltInPlanner
from .interfaces import IAgentConfig, IConfigLoader


class AgentConfig(IAgentConfig):
    """Agent configuration implementation (Single Responsibility Principle)."""
    
    def __init__(self, config_loader: IConfigLoader):
        self.config_loader = config_loader
        self.logger = logging.getLogger(__name__)
    
    def get_agent_name(self) -> str:
        """Get agent name from configuration."""
        return self.config_loader.get_value("agent.name", "enhanced_base_agent")
    
    def get_thinking_model_name(self) -> str:
        """Get thinking model name from configuration."""
        return self.config_loader.get_value("agent.thinking_model", "gemini-2.5-pro")
    
    def get_fast_model_name(self) -> str:
        """Get fast model name from configuration."""
        return self.config_loader.get_value("agent.fast_model", "gemini-2.5-flash")
    
    def get_description(self) -> str:
        """Get agent description from configuration."""
        return self.config_loader.get_value(
            "agent.description", 
            "An enhanced AI agent with advanced capabilities"
        )
    
    def get_thinking_generation_config(self) -> types.GenerateContentConfig:
        """Get thinking generation configuration."""
        thinking_generation_config = self.config_loader.get_value("agent.thinking_generation", {})
        
        return types.GenerateContentConfig(
            temperature=thinking_generation_config.get("temperature", 0.7),
            max_output_tokens=thinking_generation_config.get("max_output_tokens", 2048),
            top_p=thinking_generation_config.get("top_p", 0.9),
            top_k=thinking_generation_config.get("top_k", 40)
        )
    
    def get_fast_generation_config(self) -> types.GenerateContentConfig:
        """Get fast generation configuration."""
        fast_generation_config = self.config_loader.get_value("agent.fast_generation", {})
        
        return types.GenerateContentConfig(
            temperature=fast_generation_config.get("temperature", 0.3),
            max_output_tokens=fast_generation_config.get("max_output_tokens", 512),
            top_p=fast_generation_config.get("top_p", 0.8),
            top_k=fast_generation_config.get("top_k", 20)
        )
    
    def get_thinking_config_for_planner(self) -> Dict[str, Any]:
        """Get thinking configuration for LlmAgent planner."""
        thinking_generation_config = self.config_loader.get_value("agent.thinking_generation", {})
        thinking_budget = thinking_generation_config.get("thinking_budget")
        
        if thinking_budget is not None and thinking_budget > 0:
            # Try different ThinkingConfig configurations
            thinking_config = ThinkingConfig(
                include_thoughts=True,
                thinking_budget=thinking_budget
            )
            
            # Log the thinking config for debugging
            self.logger.info(f"ThinkingConfig created: {thinking_config}")
            
            # Create BuiltInPlanner with ThinkingConfig
            planner = BuiltInPlanner(thinking_config=thinking_config)
            
            # Log planner information
            self.logger.info(f"BuiltInPlanner created: {planner}")
            self.logger.info(f"Planner attributes: {[attr for attr in dir(planner) if not attr.startswith('_')]}")
            
            return {"planner": planner}
        
        return {}
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tools."""
        return self.config_loader.get_value("tools.enabled", [])
    
    def get_instruction(self) -> str:
        """Get agent instruction."""
        return self.config_loader.get_value(
            "agent.instruction",
            """You are an enhanced AI assistant with advanced capabilities. Your role is to:
            
            1. **Provide helpful responses**: Answer questions clearly and accurately
            2. **Use available tools**: When appropriate, use the tools at your disposal
            3. **Be structured**: When providing complex information, organize it clearly
            4. **Be helpful**: Offer additional relevant information when appropriate
            
            Guidelines:
            - Always be polite and professional
            - If you're unsure about something, say so
            - Use tools when they would genuinely help the user
            - Provide clear explanations for complex topics
            """
        )
    
    def get_system_config(self) -> Dict[str, str]:
        """Get system configuration."""
        return {
            "app_name": self.config_loader.get_value("system.app_name", "cognitive_core"),
            "user_id": self.config_loader.get_value("system.user_id", "default_user"),
            "project_id": self.config_loader.get_value("system.project_id", "genai-385616"),
            "location": self.config_loader.get_value("system.location", "us-central1")
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return {
            "host": self.config_loader.get_value("api.host", "0.0.0.0"),
            "port": self.config_loader.get_value("api.port", 8080),
            "title": self.config_loader.get_value("api.title", "Enhanced Base Agent API"),
            "description": self.config_loader.get_value("api.description", "Advanced AI agent with ADK capabilities"),
            "version": self.config_loader.get_value("api.version", "2.0.0")
        }
    
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """Get configuration for a specific tool."""
        return self.config_loader.get_value(f"tools.{tool_name}", {})
    
    def get_thinking_config(self) -> Dict[str, Any]:
        """Get thinking configuration."""
        return self.config_loader.get_value("agent.thinking", {})
    
    def is_thinking_enabled(self) -> bool:
        """Check if thinking mode is enabled."""
        thinking_generation_config = self.config_loader.get_value("agent.thinking_generation", {})
        thinking_budget = thinking_generation_config.get("thinking_budget")
        return thinking_budget is not None and thinking_budget > 0
