import gradio as gr
import requests
import json
import time
from typing import Tuple

# URL del agente base
BASE_AGENT_URL = "http://base-agent:8080"

def chat_with_agent(message: str, history: list, enable_thinking: bool):
    """
    Envía un mensaje al agente y devuelve la respuesta.
    """
    try:
        payload = {
            "message": message,
            "enable_thinking": enable_thinking
        }
        
        response = requests.post(
            f"{BASE_AGENT_URL}/chat",
            json=payload,
            timeout=60 if enable_thinking else 30
        )
        
        if response.status_code == 200:
            data = response.json()
            agent_response = data.get("response", "No response")
            
            # Agregar metadatos si están disponibles
            metadata = data.get("metadata", {})
            if metadata:
                processing_time = metadata.get("processing_time_seconds", 0)
                token_usage = metadata.get("token_usage", {})
                
                agent_response += f"\n\n⏱️ **Tiempo de procesamiento:** {processing_time}s"
                
                if token_usage:
                    prompt_tokens = token_usage.get("prompt_tokens", 0)
                    candidates_tokens = token_usage.get("candidates_tokens", 0)
                    total_tokens = token_usage.get("total_tokens", 0)
                    thoughts_tokens = token_usage.get("thoughts_tokens", 0)
                    
                    agent_response += f"\n\n🔢 **Uso de tokens:**"
                    agent_response += f"\n- Prompt: {prompt_tokens}"
                    agent_response += f"\n- Respuesta: {candidates_tokens}"
                    agent_response += f"\n- Pensamiento: {thoughts_tokens}"
                    agent_response += f"\n- **Total: {total_tokens}**"
            
            # Agregar thinking steps si están disponibles
            thinking_steps = data.get("thinking_steps", [])
            thinking_display = ""
            if thinking_steps:
                for i, step in enumerate(thinking_steps, 1):
                    thinking_display += f"**Paso {i}:**\n{step}\n\n"
            else:
                thinking_display = "*No hay proceso de pensamiento disponible*"
            
            # Actualizar historial
            history.append((message, agent_response))
            
            return "", history, thinking_display
        else:
            error_msg = f"Error HTTP {response.status_code}: {response.text}"
            history.append((message, error_msg))
            return "", history, "*Error en la comunicación con el agente*"
            
    except Exception as e:
        error_msg = f"Error connecting to agent: {str(e)}"
        history.append((message, error_msg))
        return "", history, "*Error en la comunicación con el agente*"

# Crear interfaz Gradio
with gr.Blocks(title="Cognitive Core - Agent UI") as demo:
    gr.Markdown("# 🧠 Cognitive Core - Enhanced Agent UI")
    gr.Markdown("Interfaz web para interactuar con agentes ADK mejorados con proceso de pensamiento")
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 💬 Conversación")
            chatbot = gr.Chatbot(
                label="Chat",
                height=400,
                type="tuples"
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="Escribe tu mensaje",
                    placeholder="Escribe aquí...",
                    lines=2
                )
                submit_btn = gr.Button("Enviar", variant="primary")
            
            with gr.Row():
                thinking_checkbox = gr.Checkbox(
                    label="🧠 Modo de Pensamiento Profundo",
                    value=False
                )
                clear_btn = gr.Button("Limpiar", variant="secondary")
            
            gr.Markdown("*Activar para ver el proceso de razonamiento interno (más lento pero más detallado)*")
        
        with gr.Column(scale=1):
            gr.Markdown("### 🧠 Proceso de Pensamiento")
            thinking_display = gr.Markdown(
                value="*El proceso de pensamiento aparecerá aquí después de enviar un mensaje*",
                height=500
            )
    
    # Eventos
    submit_btn.click(
        chat_with_agent,
        inputs=[msg, chatbot, thinking_checkbox],
        outputs=[msg, chatbot, thinking_display]
    )
    
    msg.submit(
        chat_with_agent,
        inputs=[msg, chatbot, thinking_checkbox],
        outputs=[msg, chatbot, thinking_display]
    )
    
    clear_btn.click(
        lambda: ([], "", "*El proceso de pensamiento aparecerá aquí después de enviar un mensaje*"),
        outputs=[chatbot, msg, thinking_display]
    )

if __name__ == "__main__":
    import os
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "7860"))
    
    demo.launch(
        server_name=host,
        server_port=port,
        share=False
    )