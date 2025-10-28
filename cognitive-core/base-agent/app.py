"""Enhanced Base Agent with SOLID architecture and configuration files."""

import os
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel as FastAPIBaseModel
import json

# Local imports
from src import (
    CompositeConfigLoader,
    YAMLConfigLoader, 
    EnvironmentConfigLoader,
    AgentConfig,
    ToolFactory,
    AgentService
)


def setup_logging(config_loader):
    """Setup logging configuration."""
    log_level = config_loader.get_value("logging.level", "INFO")
    log_format = config_loader.get_value(
        "logging.format", 
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logging.basicConfig(level=getattr(logging, log_level), format=log_format)
    return logging.getLogger(__name__)


def create_config_loader() -> CompositeConfigLoader:
    """Create composite configuration loader (Dependency Injection)."""
    config_path = os.path.join(os.path.dirname(__file__), "config", "agent_config.yaml")
    
    loaders = [
        YAMLConfigLoader(config_path),
        EnvironmentConfigLoader("AGENT_")
    ]
    
    return CompositeConfigLoader(loaders)


def create_agent_service(config_loader) -> AgentService:
    """Create agent service with dependency injection."""
    # Create agent configuration
    agent_config = AgentConfig(config_loader)
    
    # Create tool factory
    agent_info = {
        "name": agent_config.get_agent_name(),
        "version": "2.0",
        "thinking_model": agent_config.get_thinking_model_name(),
        "fast_model": agent_config.get_fast_model_name(),
        "capabilities": ["chat", "math", "time", "context_aware", "thinking_mode"],
        "tools": agent_config.get_enabled_tools()
    }
    
    tool_factory = ToolFactory(agent_config, agent_info)
    
    # Create enabled tools
    tools = tool_factory.create_all_enabled_tools()
    
    # Create agent service
    return AgentService(agent_config, tools)


# Set environment variables for ADK
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GOOGLE_CLOUD_PROJECT"] = "genai-385616"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

# Initialize application
config_loader = create_config_loader()
logger = setup_logging(config_loader)
agent_service = create_agent_service(config_loader)

# Get API configuration
api_config = agent_service.config.get_api_config()

# Create FastAPI app
app = FastAPI(
    title=api_config["title"],
    description=api_config["description"],
    version=api_config["version"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(FastAPIBaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    enable_thinking: Optional[bool] = None

class ChatResponse(FastAPIBaseModel):
    response: str
    session_id: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    thinking_steps: Optional[List[str]] = None


# API endpoints
@app.get("/health")
async def health():
    """Health check endpoint."""
    from datetime import datetime
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint with agent information."""
    system_config = agent_service.config.get_system_config()
    return {
        "name": agent_service.config.get_agent_name(),
        "model": agent_service.config.get_model_name(),
        "status": "running",
        "project_id": system_config["project_id"],
        "location": system_config["location"],
        "capabilities": ["chat", "math", "time", "context_aware", "tools"],
        "tools_count": len([t for t in agent_service.tools if t.is_enabled()])
    }

@app.get("/agent/info")
async def get_agent_info():
    """Get detailed agent information."""
    return agent_service.get_agent_info()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Enhanced chat endpoint with SOLID architecture."""
    try:
        # Use provided session_id or generate a new one
        from datetime import datetime
        current_session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Process message using agent service with thinking control
        result = await agent_service.process_message(
            request.message, 
            current_session_id, 
            enable_thinking=request.enable_thinking
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint with real-time thinking steps."""
    async def generate_stream():
        try:
            # Use provided session_id or generate a new one
            from datetime import datetime
            current_session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Process message with streaming
            async for chunk in agent_service.process_message_streaming(
                request.message, 
                current_session_id, 
                enable_thinking=request.enable_thinking
            ):
                # Format as Server-Sent Events
                yield f"data: {json.dumps(chunk)}\n\n"
                
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            error_chunk = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.get("/sessions/{session_id}/state")
async def get_session_state(session_id: str):
    """Get the current state of a session."""
    try:
        session = await agent_service.session_service.get_session(
            app_name=agent_service.app_name,
            user_id=agent_service.user_id,
            session_id=session_id
        )
        return {
            "session_id": session_id,
            "state": session.state,
            "created_at": getattr(session, 'created_at', 'unknown')
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    host = api_config["host"]
    port = api_config["port"]
    
    logger.info(f"Starting Enhanced Base Agent on {host}:{port}")
    logger.info(f"Agent capabilities: {[tool.name for tool in agent_service.tools if tool.is_enabled()]}")
    
    uvicorn.run(app, host=host, port=port)