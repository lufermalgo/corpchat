"""Agent service implementation following SOLID principles."""

import logging
import time
from typing import Dict, Any, List
from datetime import datetime
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types
from .interfaces import IAgentService, ITool
from .agent_config import AgentConfig


class AgentService(IAgentService):
    """Agent service implementation (Single Responsibility Principle)."""
    
    def __init__(self, config: AgentConfig, tools: List[ITool]):
        self.config = config
        self.tools = tools
        self.logger = logging.getLogger(__name__)
        
        # Initialize ADK components
        self._setup_agents()
        self._setup_session_service()
        self._setup_runners()
    
    def _setup_agents(self):
        """Setup both ADK agents - one with thinking, one without."""
        # Convert ITool instances to FunctionTool for ADK
        adk_tools = []
        for tool in self.tools:
            if tool.is_enabled():
                adk_tools.append(FunctionTool(self._create_tool_wrapper(tool)))
        
        # Agent WITH thinking (using BuiltInPlanner with ThinkingConfig)
        planner_config = self.config.get_thinking_config_for_planner()
        self.agent_with_thinking = LlmAgent(
            name=f"{self.config.get_agent_name()}_thinking",
            model=self.config.get_thinking_model_name(),  # Usar modelo de thinking
            description=self.config.get_description(),
            instruction=self.config.get_instruction(),
            tools=adk_tools,
            generate_content_config=self.config.get_thinking_generation_config(),  # Usar configuración de thinking
            **planner_config
        )
        
        # Agent WITHOUT thinking (using default planner and faster model)
        self.agent_without_thinking = LlmAgent(
            name=f"{self.config.get_agent_name()}_fast",
            model=self.config.get_fast_model_name(),  # Usar modelo rápido
            description=self.config.get_description(),
            instruction=self.config.get_instruction(),
            tools=adk_tools,
            generate_content_config=self.config.get_fast_generation_config()  # Usar configuración rápida
        )
        
        self.logger.info(f"Agent '{self.config.get_agent_name()}' initialized with {len(adk_tools)} tools")
        self.logger.info("Created two agents: one with thinking, one without")
    
    def _setup_session_service(self):
        """Setup session service."""
        system_config = self.config.get_system_config()
        self.session_service = InMemorySessionService()
        self.app_name = system_config["app_name"]
        self.user_id = system_config["user_id"]
    
    def _setup_runners(self):
        """Setup both runners."""
        self.runner_with_thinking = Runner(
            agent=self.agent_with_thinking,
            app_name=self.app_name,
            session_service=self.session_service
        )
        
        self.runner_without_thinking = Runner(
            agent=self.agent_without_thinking,
            app_name=self.app_name,
            session_service=self.session_service
        )
    
    def _create_tool_wrapper(self, tool: ITool):
        """Create a wrapper function for ITool to work with ADK FunctionTool."""
        def wrapper(expression: str = "", **kwargs):
            # For math tool, pass the expression parameter
            if tool.name == "calculate_math":
                result = tool.execute(expression=expression, **kwargs)
            else:
                result = tool.execute(**kwargs)
            
            if result.success:
                return result.result
            else:
                return f"Error: {result.error}"
        
        # Set function metadata for ADK
        wrapper.__name__ = tool.name
        wrapper.__doc__ = tool.description
        
        return wrapper
    
    async def process_message_streaming(self, message: str, session_id: str, enable_thinking: bool = None):
        """Process a message with streaming thinking steps."""
        start_time = time.time()
        
        try:
            # Determine if thinking should be enabled
            thinking_enabled = enable_thinking if enable_thinking is not None else self.config.is_thinking_enabled()
            
            self.logger.info(f"Processing message with streaming thinking_enabled={thinking_enabled}")
            
            # Create or get session - use the same approach as working method
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=session_id
            )
            
            # Create message content
            content = types.Content(
                role='user',
                parts=[types.Part(text=message)]
            )
            
            # Choose the appropriate runner based on thinking mode
            if thinking_enabled:
                self.logger.info("Using agent WITH thinking (streaming)")
                events = self.runner_with_thinking.run_async(
                    user_id=self.user_id,
                    session_id=session_id,
                    new_message=content
                )
            else:
                self.logger.info("Using agent WITHOUT thinking (streaming)")
                events = self.runner_without_thinking.run_async(
                    user_id=self.user_id,
                    session_id=session_id,
                    new_message=content
                )
            
            # Stream results
            final_response = "No response received"
            thinking_steps = []
            metadata = {
                "events_processed": 0, 
                "tools_used": [], 
                "thinking_enabled": thinking_enabled,
                "processing_time_seconds": 0,
                "token_usage": {}
            }
            
            async for event in events:
                metadata["events_processed"] += 1
                
                # Check for thinking content in real-time
                if thinking_enabled and hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'thought') and part.thought and hasattr(part, 'text') and part.text:
                            thinking_step = f"🧠 **Proceso de Pensamiento:**\n{part.text.strip()}"
                            thinking_steps.append(thinking_step)
                            
                            # Yield thinking step immediately
                            yield {
                                "type": "thinking",
                                "content": thinking_step,
                                "step_number": len(thinking_steps)
                            }
                
                # Check for usage_metadata
                if hasattr(event, 'usage_metadata') and event.usage_metadata:
                    metadata["token_usage"] = {
                        "prompt_tokens": event.usage_metadata.prompt_token_count,
                        "candidates_tokens": event.usage_metadata.candidates_token_count,
                        "total_tokens": event.usage_metadata.total_token_count,
                        "thoughts_tokens": getattr(event.usage_metadata, 'thoughts_token_count', 0)
                    }
                
                # Track tool usage
                if hasattr(event, 'tool_calls') and event.tool_calls:
                    for tool_call in event.tool_calls:
                        metadata["tools_used"].append(tool_call.name)
                        yield {
                            "type": "tool_usage",
                            "tool_name": tool_call.name
                        }
                
                if event.is_final_response() and event.content and event.content.parts:
                    # Process response parts
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response = part.text
                            
                            # Yield final response
                            yield {
                                "type": "response",
                                "content": final_response
                            }
            
            # Calculate processing time
            end_time = time.time()
            processing_time = end_time - start_time
            metadata["processing_time_seconds"] = round(processing_time, 2)
            
            # Yield final metadata
            yield {
                "type": "metadata",
                "metadata": metadata,
                "thinking_steps": thinking_steps if thinking_steps else None
            }
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    async def process_message(self, message: str, session_id: str, enable_thinking: bool = None) -> Dict[str, Any]:
        """Process a message using the agent."""
        start_time = time.time()
        
        try:
            # Determine if thinking should be enabled
            thinking_enabled = enable_thinking if enable_thinking is not None else self.config.is_thinking_enabled()
            
            self.logger.info(f"Processing message with thinking_enabled={thinking_enabled}")
            
            # Create or get session
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=session_id
            )
            
            # Create message content
            content = types.Content(
                role='user',
                parts=[types.Part(text=message)]
            )
            
            # Choose the appropriate runner based on thinking mode
            if thinking_enabled:
                self.logger.info("Using agent WITH thinking")
                events = self.runner_with_thinking.run_async(
                    user_id=self.user_id,
                    session_id=session_id,
                    new_message=content
                )
            else:
                self.logger.info("Using agent WITHOUT thinking")
                events = self.runner_without_thinking.run_async(
                    user_id=self.user_id,
                    session_id=session_id,
                    new_message=content
                )
            
            self.logger.info("Starting to process events with detailed logging...")
            
            # Collect results
            final_response = "No response received"
            thinking_steps = []
            metadata = {
                "events_processed": 0, 
                "tools_used": [], 
                "thinking_enabled": thinking_enabled,
                "processing_time_seconds": 0,
                "token_usage": {}
            }
            
            async for event in events:
                metadata["events_processed"] += 1
                
                # Debug: Log all event information
                self.logger.info(f"Event type: {type(event)}")
                
                # Check for logprobs_result which might contain thinking content
                if hasattr(event, 'logprobs_result') and event.logprobs_result:
                    self.logger.info(f"Logprobs result found: {event.logprobs_result}")
                    thinking_steps.append(f"[LOGPROBS] {str(event.logprobs_result)}")
                
                # Check for usage_metadata
                if hasattr(event, 'usage_metadata') and event.usage_metadata:
                    self.logger.info(f"Usage metadata: {event.usage_metadata}")
                    # Capture token usage information
                    metadata["token_usage"] = {
                        "prompt_tokens": event.usage_metadata.prompt_token_count,
                        "candidates_tokens": event.usage_metadata.candidates_token_count,
                        "total_tokens": event.usage_metadata.total_token_count,
                        "thoughts_tokens": getattr(event.usage_metadata, 'thoughts_token_count', 0)
                    }
                
                # Check for custom_metadata
                if hasattr(event, 'custom_metadata') and event.custom_metadata:
                    self.logger.info(f"Custom metadata: {event.custom_metadata}")
                
                # Check if this event has thinking content
                if hasattr(event, 'content') and event.content:
                    self.logger.info(f"Event content type: {type(event.content)}")
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for i, part in enumerate(event.content.parts):
                            self.logger.info(f"Part {i} type: {type(part)}")
                            
                            # Try to get more information from the part
                            if hasattr(part, 'to_json_dict'):
                                try:
                                    part_dict = part.to_json_dict()
                                    self.logger.info(f"Part {i} JSON dict: {part_dict}")
                                except Exception as e:
                                    self.logger.info(f"Error getting part {i} JSON dict: {e}")
                            
                            if hasattr(part, 'model_dump'):
                                try:
                                    part_dump = part.model_dump()
                                    self.logger.info(f"Part {i} model dump: {part_dump}")
                                except Exception as e:
                                    self.logger.info(f"Error getting part {i} model dump: {e}")
                
                if event.is_final_response() and event.content and event.content.parts:
                    # Process response parts
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response = part.text
                        # Check for thinking steps if thinking is enabled
                        if thinking_enabled:
                            # The real thinking content is in the 'text' field when 'thought' is True
                            if hasattr(part, 'thought') and part.thought and hasattr(part, 'text') and part.text:
                                # This is the actual thinking content!
                                thinking_steps.append(f"🧠 **Proceso de Pensamiento:**\n{part.text.strip()}")
                                self.logger.info(f"Found real thinking content: {part.text[:100]}...")
                            
                            # Also check for thought_signature (metadata)
                            elif hasattr(part, 'thought_signature') and part.thought_signature:
                                if isinstance(part.thought_signature, str):
                                    # This is the signature/metadata
                                    thinking_steps.append(f"📝 **Firma de Pensamiento:** {part.thought_signature[:50]}...")
                                else:
                                    thinking_steps.append(f"📝 **Metadatos de Pensamiento:** {len(part.thought_signature)} bytes")
                    
                    self.logger.info(f"Final response: {final_response}")
                    if thinking_steps:
                        self.logger.info(f"Thinking steps captured: {len(thinking_steps)}")
                        # Log the actual thinking content for debugging
                        for i, step in enumerate(thinking_steps):
                            self.logger.info(f"Thinking step {i+1}: {str(step)[:200]}...")
                
                # Track tool usage
                if hasattr(event, 'tool_calls') and event.tool_calls:
                    for tool_call in event.tool_calls:
                        metadata["tools_used"].append(tool_call.name)
            
            # Get updated session state
            updated_session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=session_id
            )
            
            metadata["session_state_keys"] = list(updated_session.state.keys())
            
            # Calculate processing time
            end_time = time.time()
            processing_time = end_time - start_time
            metadata["processing_time_seconds"] = round(processing_time, 2)
            
            result = {
                "response": final_response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata
            }
            
            # Add thinking steps if available
            if thinking_steps:
                # Ensure thinking steps are JSON serializable
                serializable_thinking_steps = []
                for i, step in enumerate(thinking_steps):
                    try:
                        # Convert to string and ensure it's serializable
                        serializable_step = str(step)
                        serializable_thinking_steps.append(serializable_step)
                    except Exception as e:
                        serializable_thinking_steps.append(f"[Error serializing thinking step {i+1}: {str(e)}]")
                
                result["thinking_steps"] = serializable_thinking_steps
                metadata["thinking_steps_count"] = len(serializable_thinking_steps)
                self.logger.info(f"Added {len(serializable_thinking_steps)} thinking steps to response")
            else:
                self.logger.info("No thinking steps to add to response")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            raise
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "agent": {
                "name": self.config.get_agent_name(),
                "model": self.config.get_model_name(),
                "description": self.config.get_description(),
                "tools": [tool.name for tool in self.tools if tool.is_enabled()],
                "capabilities": [
                    "Natural language processing",
                    "Mathematical calculations", 
                    "Time queries",
                    "Context management",
                    "Structured responses"
                ]
            },
            "configuration": self.config.get_system_config()
        }
