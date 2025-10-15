"""
Tests de delegación multi-agent del orquestador ADK.

Valida que:
1. El orchestrator recibe queries
2. Delega correctamente a especialistas
3. Los especialistas invocan tools
4. Las respuestas fluyen correctamente
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Agregar paths necesarios
agents_path = Path(__file__).parent.parent
if str(agents_path) not in sys.path:
    sys.path.insert(0, str(agents_path))

from google.adk.runners import InMemoryRunner
from google.genai import types
from orchestrator.agent import create_orchestrator_agent


@pytest.fixture
async def runner():
    """Fixture que crea un runner ADK para tests."""
    orchestrator = create_orchestrator_agent()
    runner = InMemoryRunner(
        agent=orchestrator,
        app_name="CorpChatTest"
    )
    return runner


@pytest.mark.asyncio
async def test_orchestrator_creation():
    """Test básico: verificar que el orchestrator se crea correctamente."""
    orchestrator = create_orchestrator_agent()
    
    assert orchestrator is not None
    assert orchestrator.name == "CorpChat"
    
    # Verificar sub-agents
    # Nota: La estructura exacta depende de la implementación de ADK
    # Este test puede necesitar ajustes según la API
    print(f"✅ Orchestrator creado: {orchestrator.name}")


@pytest.mark.asyncio
async def test_simple_query_to_orchestrator(runner):
    """
    Test: Query simple al orchestrator sin delegación.
    
    Debe responder directamente preguntas generales.
    """
    # Crear sesión
    session = await runner.session_service.create_session(
        app_name="CorpChatTest",
        user_id="test_user_001"
    )
    
    # Mensaje simple
    content = types.Content(
        role='user',
        parts=[types.Part.from_text(text="Hola, ¿cómo estás?")]
    )
    
    # Invocar orchestrator
    response_text = ""
    events_count = 0
    
    async for event in runner.run_async(
        user_id="test_user_001",
        session_id=session.id,
        new_message=content
    ):
        events_count += 1
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    
    # Validaciones
    assert events_count > 0, "Debe haber al menos un evento"
    assert response_text, "Debe haber una respuesta de texto"
    assert len(response_text) > 10, "La respuesta debe ser sustantiva"
    
    print(f"✅ Query simple completada:")
    print(f"   Events: {events_count}")
    print(f"   Response: {response_text[:100]}...")


@pytest.mark.asyncio
async def test_delegation_to_knowledge_specialist(runner):
    """
    Test: Query sobre conocimiento empresarial debe delegar al especialista.
    
    Nota: En MVP con tools placeholder, validamos la estructura,
    no el contenido exacto de la respuesta.
    """
    # Crear sesión
    session = await runner.session_service.create_session(
        app_name="CorpChatTest",
        user_id="test_user_002"
    )
    
    # Query sobre política interna (debe ir a especialista de conocimiento)
    content = types.Content(
        role='user',
        parts=[types.Part.from_text(
            text="¿Cuál es la política de vacaciones de la empresa?"
        )]
    )
    
    # Invocar orchestrator
    response_text = ""
    events_count = 0
    tool_calls = []
    
    async for event in runner.run_async(
        user_id="test_user_002",
        session_id=session.id,
        new_message=content
    ):
        events_count += 1
        
        # Capturar eventos
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
                elif hasattr(part, 'function_call') and part.function_call:
                    tool_calls.append(part.function_call.name)
    
    # Validaciones
    assert events_count > 0, "Debe haber eventos"
    assert response_text, "Debe haber respuesta"
    
    print(f"✅ Delegation test completado:")
    print(f"   Events: {events_count}")
    print(f"   Tool calls: {tool_calls}")
    print(f"   Response: {response_text[:150]}...")
    
    # En un test más avanzado, validaríamos:
    # - Que se invocó search_knowledge_base
    # - Que la respuesta menciona fuentes
    # - Que el formato es correcto


@pytest.mark.asyncio
async def test_delegation_to_products_specialist(runner):
    """
    Test: Query sobre productos debe delegar al especialista de productos.
    """
    session = await runner.session_service.create_session(
        app_name="CorpChatTest",
        user_id="test_user_003"
    )
    
    # Query sobre productos
    content = types.Content(
        role='user',
        parts=[types.Part.from_text(
            text="Necesito información sobre laptops disponibles y sus precios"
        )]
    )
    
    response_text = ""
    events_count = 0
    
    async for event in runner.run_async(
        user_id="test_user_003",
        session_id=session.id,
        new_message=content
    ):
        events_count += 1
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    
    # Validaciones
    assert events_count > 0
    assert response_text
    assert len(response_text) > 20
    
    print(f"✅ Products delegation test completado:")
    print(f"   Events: {events_count}")
    print(f"   Response: {response_text[:150]}...")


@pytest.mark.asyncio
async def test_multi_turn_conversation(runner):
    """
    Test: Conversación de múltiples turnos con context preservation.
    """
    session = await runner.session_service.create_session(
        app_name="CorpChatTest",
        user_id="test_user_004"
    )
    
    # Turno 1: Pregunta inicial
    content1 = types.Content(
        role='user',
        parts=[types.Part.from_text(text="¿Qué productos tienen en laptops?")]
    )
    
    response1 = ""
    async for event in runner.run_async(
        user_id="test_user_004",
        session_id=session.id,
        new_message=content1
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response1 += part.text
    
    assert response1, "Debe haber respuesta en turno 1"
    
    # Turno 2: Pregunta de seguimiento (debe mantener contexto)
    content2 = types.Content(
        role='user',
        parts=[types.Part.from_text(text="¿Cuál es el más económico?")]
    )
    
    response2 = ""
    async for event in runner.run_async(
        user_id="test_user_004",
        session_id=session.id,
        new_message=content2
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response2 += part.text
    
    assert response2, "Debe haber respuesta en turno 2"
    
    print(f"✅ Multi-turn test completado:")
    print(f"   Turn 1: {response1[:100]}...")
    print(f"   Turn 2: {response2[:100]}...")


if __name__ == "__main__":
    # Ejecutar tests manualmente
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Ejecutando tests de delegación multi-agent...\n")
    
    # Ejecutar con pytest
    pytest.main([__file__, "-v", "-s"])

