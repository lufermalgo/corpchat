# services/backend/src/generalist/agent.py

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google.adk.agents import LlmAgent
from shared.config import MODEL_CONFIG, AGENT_CONFIG, PROMPTS_CONFIG, GCP_PROJECT_ID

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

# --- Generalist Agent Definition ---
# Load generalist configuration from YAML
generalist_config = AGENT_CONFIG.get('generalist', {})
# Get prompts from configuration using prompt_ref
prompt_ref = generalist_config.get('prompt_ref', 'generalist')
generalist_prompts = PROMPTS_CONFIG.get(prompt_ref, {})

generalist_agent = LlmAgent(
    name=generalist_config.get('name', 'generalist_agent'),
    model=generalist_config.get('default_model', "gemini-2.5-flash-lite"),  # Default model, will be overridden dynamically
    instruction=generalist_prompts.get('system', 'Default generalist instruction'),
    description=generalist_config.get('description', "A generalist agent that processes requests using different AI models based on user selection.")
)

# --- FastAPI Server Setup ---
if __name__ == "__main__":
    _logger.info("Starting Generalist FastAPI Server with ADK...")
    _logger.info(f"Available models: {list(MODEL_CONFIG.keys())}")
    
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    import uvicorn
    
    app = FastAPI(title="CorpChat Generalist", version="1.0.0")
    
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        """Handle chat completions using ADK generalist agent"""
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
            _logger.info(f"Generalist received message: '{message}' with model: {model_id} ({model_config['display_name']})")
            
            # Configure the agent with the selected model
            generalist_agent.model = model_config['llm_model']
            _logger.info(f"Configured generalist agent with model: {model_config['llm_model']}")
            
            # Use ADK generalist agent to process the message
            response_chunks = []
            try:
                # Use the generalist agent's run_async method
                async for chunk in generalist_agent.run_async(message):
                    if hasattr(chunk, 'content') and chunk.content:
                        response_chunks.append(chunk.content)
                    elif isinstance(chunk, str):
                        response_chunks.append(chunk)
                
                # Combine all response chunks
                response_text = "".join(response_chunks) if response_chunks else "No response generated"
                
            except Exception as adk_error:
                _logger.warning(f"ADK agent processing failed: {adk_error}. Using direct model call.")
                # Fallback to direct Vertex AI call if ADK fails
                import vertexai
                from vertexai.generative_models import GenerativeModel
                
                # Initialize Vertex AI
                vertexai.init(project=GCP_PROJECT_ID, location="us-central1")
                
                # Create model instance using the selected model
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
            
            return JSONResponse(content={
                "choices": [{
                    "message": {
                        "content": response_text,
                        "role": "assistant"
                    }
                }]
            })
            
        except Exception as e:
            _logger.error(f"Error during Generalist processing: {e}", exc_info=True)
            return JSONResponse(content={"error": f"An unexpected error occurred: {e}"}, status_code=500)
    
    _logger.info("Generalist FastAPI Server started on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)