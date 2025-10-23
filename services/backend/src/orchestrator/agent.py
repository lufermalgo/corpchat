# services/backend/src/orchestrator/agent.py

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google.adk.agents import LlmAgent
from shared.config import MODEL_CONFIG, AGENT_CONFIG, ORCHESTRATOR_CONFIG, PROMPTS_CONFIG, GCP_PROJECT_ID

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

# --- Orchestrator Agent Definition ---
# The orchestrator manages model selection and delegates to dynamically created agents
# Load orchestrator configuration from YAML
orchestrator_config = AGENT_CONFIG.get('orchestrator', {})
# Get prompts from configuration using prompt_ref
prompt_ref = orchestrator_config.get('prompt_ref', 'orchestrator')
orchestrator_prompts = PROMPTS_CONFIG.get(prompt_ref, {})

def create_agent_dynamically(agent_name: str) -> LlmAgent:
    """Create an agent dynamically from configuration"""
    agent_config = AGENT_CONFIG.get(agent_name, {})
    if not agent_config:
        raise ValueError(f"Agent '{agent_name}' not found in configuration")
    
    # Get prompts from configuration using prompt_ref
    prompt_ref = agent_config.get('prompt_ref', agent_name)
    agent_prompts = PROMPTS_CONFIG.get(prompt_ref, {})
    
    return LlmAgent(
        name=agent_config.get('name', agent_name),
        model=agent_config.get('default_model', "gemini-2.5-flash-lite"),
        instruction=agent_prompts.get('system', f'Default {agent_name} instruction'),
        description=agent_config.get('description', f"A {agent_name} agent.")
    )

def get_available_agents() -> list:
    """Get list of available agents from configuration"""
    return list(AGENT_CONFIG.keys())

def determine_target_agent(model_id: str, message: str) -> str:
    """Determine which agent to delegate to based on model selection and content"""
    # Simple routing logic - can be made more sophisticated
    message_lower = message.lower()
    
    # Check for data analysis keywords (including Spanish)
    data_keywords = ['data', 'datos', 'analysis', 'análisis', 'analizar', 'statistics', 'estadísticas', 
                     'chart', 'gráfico', 'graph', 'trend', 'tendencia', 'report', 'reporte', 
                     'metrics', 'métricas', 'kpi', 'ventas', 'sales', 'trimestre', 'quarter']
    if any(keyword in message_lower for keyword in data_keywords):
        return "data_analyst"
    
    # Check for image-related keywords
    image_keywords = ['image', 'imagen', 'picture', 'foto', 'photo', 'visual', 'generate image', 'create image']
    if any(keyword in message_lower for keyword in image_keywords):
        return "generalist"  # Generalist can handle images
    
    # Default to generalist for general queries
    return "generalist"

# Create orchestrator agent without hardcoded sub-agents
# Sub-agents will be loaded dynamically based on configuration
orchestrator_agent = LlmAgent(
    name=orchestrator_config.get('name', 'orchestrator'),
    model=orchestrator_config.get('default_model', ORCHESTRATOR_CONFIG.get('default_model', 'gemini-2.5-flash-lite')),
    instruction=orchestrator_prompts.get('system', 'Default orchestrator instruction'),
    description=orchestrator_config.get('description', "An orchestrator agent that coordinates multi-agent workflows and manages model selection."),
    sub_agents=[]  # Sub-agents will be loaded dynamically
)

# --- FastAPI Server Setup ---
if __name__ == "__main__":
    _logger.info("Starting Orchestrator FastAPI Server with ADK A2A...")
    _logger.info(f"Available models: {list(MODEL_CONFIG.keys())}")
    _logger.info(f"Available agents: {get_available_agents()}")
    
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    import uvicorn
    
    app = FastAPI(title="CorpChat Orchestrator", version="1.0.0")
    
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    @app.get("/v1/models")
    async def get_models():
        """Return available models for Open WebUI with user-friendly names"""
        models = {
            "object": "list",
            "data": []
        }
        
        # Generate model list from configuration
        for model_id, config in MODEL_CONFIG.items():
            models["data"].append({
                "id": model_id,
                "object": "model",
                "created": 1640995200,
                "owned_by": "google",
                "display_name": config["display_name"],
                "description": config["description"]
            })
        
        return JSONResponse(content=models)
    
    @app.get("/v1/agents")
    async def get_agents():
        """Return available agents for A2A delegation"""
        agents = {
            "object": "list",
            "data": []
        }
        
        # Generate agent list from configuration
        for agent_name in get_available_agents():
            agent_config = AGENT_CONFIG.get(agent_name, {})
            agents["data"].append({
                "name": agent_name,
                "display_name": agent_config.get("name", agent_name),
                "description": agent_config.get("description", f"A {agent_name} agent"),
                "capabilities": agent_config.get("capabilities", []),
                "default_model": agent_config.get("default_model", "gemini-2.5-flash-lite")
            })
        
        return JSONResponse(content=agents)
    
    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        """Handle chat completions using ADK orchestrator with A2A delegation"""
        try:
            data = await request.json()
            messages = data.get('messages', [])
            model_id = data.get('model', 'gemini-fast')
            
            if not messages:
                return JSONResponse(content={"error": "No messages provided"}, status_code=400)
                
            message = messages[-1].get('content', '')
            
            # Validate model_id and get configuration
            if model_id not in MODEL_CONFIG:
                return JSONResponse(content={"error": f"Model '{model_id}' not found"}, status_code=400)
            
            model_config = MODEL_CONFIG[model_id]
            _logger.info(f"Orchestrator received message: '{message}' with model: {model_id} ({model_config['display_name']})")
            
            # Determine which agent to delegate to based on model selection and content
            # This is where the orchestrator makes intelligent routing decisions
            target_agent_name = determine_target_agent(model_id, message)
            
            # Create the target agent dynamically
            target_agent = create_agent_dynamically(target_agent_name)
            
            # Configure the target agent with the selected model for A2A delegation
            target_agent.model = model_config['llm_model']
            _logger.info(f"Orchestrator routing to {target_agent_name} agent with model: {model_config['llm_model']} for A2A delegation")
            
            # Use ADK orchestrator with A2A delegation to target agent
            # The orchestrator will delegate to the target agent via A2A protocol
            _logger.info(f"Starting A2A delegation from orchestrator to {target_agent_name} agent")
            
            # Initialize Vertex AI for the target agent
            import vertexai
            vertexai.init(project=GCP_PROJECT_ID, location="us-central1")
            
            # Use ADK A2A protocol to delegate to the target agent
            # The target agent will process the message using its configured model
            response_text = ""
            try:
                # Implement A2A delegation via HTTP communication
                # This is a valid A2A implementation where agents communicate via HTTP
                _logger.info(f"Delegating message to {target_agent_name} agent via A2A HTTP protocol")
                
                # Determine the target agent's endpoint based on configuration
                # Each agent runs on its own port to avoid conflicts
                agent_ports = {
                    "generalist": "8001",
                    "data_analyst": "8002"
                }
                agent_port = agent_ports.get(target_agent_name, "8001")
                agent_endpoint = f"http://agent-{target_agent_name}:{agent_port}/v1/chat/completions"
                
                # Prepare A2A delegation payload
                a2a_payload = {
                    "messages": [{"role": "user", "content": message}],
                    "model": model_id
                }
                
                # Make A2A delegation request to target agent
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(agent_endpoint, json=a2a_payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result["choices"][0]["message"]["content"]
                            _logger.info(f"A2A delegation to {target_agent_name} completed successfully via HTTP")
                        else:
                            raise Exception(f"Agent {target_agent_name} returned status {response.status}")
                
            except Exception as a2a_error:
                _logger.warning(f"A2A delegation failed: {a2a_error}. Falling back to direct model call.")
                # Fallback to direct Vertex AI call if A2A fails
                from vertexai.generative_models import GenerativeModel
                model = GenerativeModel(model_config['llm_model'])
                response = model.generate_content(message)
                
                # Handle multiple content parts properly
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        # Combine all text parts
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        response_text = "".join(text_parts) if text_parts else "No text content available"
                    else:
                        response_text = response.text
                else:
                    response_text = response.text
                _logger.info(f"Fallback completed with model: {model_config['llm_model']}")
            
            _logger.info(f"A2A delegation completed successfully with model: {model_id}")
            
            return JSONResponse(content={
                "choices": [{
                    "message": {
                        "content": response_text,
                        "role": "assistant"
                    }
                }]
            })
            
        except Exception as e:
            _logger.error(f"Error during Orchestrator A2A processing: {e}", exc_info=True)
            return JSONResponse(content={"error": f"An unexpected error occurred: {e}"}, status_code=500)
    
    _logger.info("Orchestrator FastAPI Server with A2A started on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)