#!/usr/bin/env python3
"""
Main entry point for the Cognitive Core application.
Simplified version for testing basic functionality.
"""

import logging
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Cognitive Core API",
    description="Multi-agent cognitive core with ADK and A2A Protocol",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Cognitive Core API",
        "version": "1.0.0",
        "status": "running",
        "note": "Simplified version for testing"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "cognitive_core": "simplified_mode"
    }

@app.post("/process")
async def process_request(request_data: Dict[str, Any]):
    """Process a request through the cognitive core."""
    _logger.info(f"Processing request: {request_data}")
    
    # Simple echo response for testing
    return {
        "status": "success",
        "message": "Request processed successfully",
        "input": request_data,
        "note": "This is a simplified response for testing"
    }

@app.get("/agents")
async def list_agents():
    """List available agents."""
    return {
        "agents": [
            {
                "id": "test-agent",
                "name": "Test Agent",
                "description": "Simplified test agent",
                "status": "available"
            }
        ]
    }

@app.get("/agents/{agent_id}")
async def get_agent_info(agent_id: str):
    """Get information about a specific agent."""
    return {
        "id": agent_id,
        "name": f"Agent {agent_id}",
        "description": "Simplified test agent",
        "status": "available",
        "capabilities": ["basic_processing"]
    }

if __name__ == "__main__":
    _logger.info("Starting Cognitive Core in simplified mode...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )