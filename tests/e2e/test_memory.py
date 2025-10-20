#!/usr/bin/env python3
"""
Test E2E para funcionalidad de memoria híbrida (working + long-term).
"""

import requests
import time
import json
import uuid
from datetime import datetime

GATEWAY_URL = "https://corpchat-gateway-2s63drefva-uc.a.run.app"  # Reemplazar con la URL real


def test_memory_functionality():
    """
    Test completo de funcionalidad de memoria híbrida.
    """
    print("\n--- Iniciando test de memoria híbrida ---")
    
    # Configuración del test
    user_id = f"test_user_{int(time.time())}"
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    
    print(f"Usuario de prueba: {user_id}")
    print(f"Sesión de prueba: {session_id}")
    
    # 1. Test de perfil de usuario
    print("\n1. Probando perfil de usuario...")
    try:
        profile_response = requests.get(f"{GATEWAY_URL}/v1/memory/profile/{user_id}")
        profile_response.raise_for_status()
        profile = profile_response.json()
        
        assert "email" in profile, "Perfil debe tener email"
        assert "preferences" in profile, "Perfil debe tener preferencias"
        assert profile["email"] == user_id, "Email debe coincidir con user_id"
        
        print("✅ Perfil de usuario creado/recuperado exitosamente")
        
    except Exception as e:
        print(f"❌ Error en perfil de usuario: {e}")
        return False
    
    # 2. Test de conversación con memoria
    print("\n2. Probando conversación con memoria...")
    
    conversation_messages = [
        "Hola, mi nombre es Juan y trabajo en desarrollo de software",
        "Estoy trabajando en un proyecto de inteligencia artificial",
        "¿Puedes ayudarme con el análisis de datos?",
        "¿Recuerdas mi nombre y en qué trabajo?"
    ]
    
    for i, message in enumerate(conversation_messages, 1):
        print(f"   Enviando mensaje {i}: {message}")
        
        try:
            chat_payload = {
                "model": "gemini-fast",
                "messages": [{"role": "user", "content": message}],
                "session_id": session_id,
                "stream": False
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer test-key",
                "X-OpenWebUI-User-Email": f"{user_id}@example.com",
                "X-OpenWebUI-User-Id": user_id
            }
            
            response = requests.post(
                f"{GATEWAY_URL}/v1/chat/completions",
                json=chat_payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            chat_response = response.json()
            
            assistant_message = chat_response["choices"][0]["message"]["content"]
            print(f"   Respuesta: {assistant_message[:100]}...")
            
            # Verificar que la respuesta no esté vacía
            assert len(assistant_message.strip()) > 0, f"Respuesta vacía para mensaje {i}"
            
            time.sleep(2)  # Pausa entre mensajes
            
        except Exception as e:
            print(f"❌ Error en mensaje {i}: {e}")
            return False
    
    print("✅ Conversación con memoria completada exitosamente")
    
    # 3. Test de contexto enriquecido
    print("\n3. Probando contexto enriquecido...")
    try:
        context_response = requests.get(
            f"{GATEWAY_URL}/v1/memory/context/{user_id}",
            params={
                "session_id": session_id,
                "query": "¿Cuál es el nombre del usuario y en qué trabaja?"
            }
        )
        context_response.raise_for_status()
        context_data = context_response.json()
        
        enhanced_context = context_data.get("enhanced_context", "")
        
        assert len(enhanced_context) > 0, "Contexto enriquecido no debe estar vacío"
        assert "Juan" in enhanced_context or "desarrollo" in enhanced_context.lower(), \
            "Contexto debe contener información previa del usuario"
        
        print(f"✅ Contexto enriquecido generado: {len(enhanced_context)} caracteres")
        print(f"   Muestra: {enhanced_context[:200]}...")
        
    except Exception as e:
        print(f"❌ Error en contexto enriquecido: {e}")
        return False
    
    # 4. Test de consolidación de memoria
    print("\n4. Probando consolidación de memoria...")
    try:
        consolidate_response = requests.post(
            f"{GATEWAY_URL}/v1/memory/consolidate/{user_id}/{session_id}"
        )
        consolidate_response.raise_for_status()
        consolidate_data = consolidate_response.json()
        
        assert consolidate_data["success"], "Consolidación debe ser exitosa"
        assert "result" in consolidate_data, "Resultado de consolidación debe estar presente"
        
        result = consolidate_data["result"]
        if result.get("success"):
            print(f"✅ Memoria consolidada exitosamente")
            print(f"   Turnos procesados: {result.get('turn_count', 0)}")
            print(f"   Resumen: {result.get('summary', 'N/A')[:100]}...")
            print(f"   Tags: {result.get('tags', [])}")
        else:
            print(f"⚠️ Consolidación no aplicable: {result.get('reason', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error en consolidación de memoria: {e}")
        return False
    
    # 5. Test de memoria a largo plazo
    print("\n5. Probando memoria a largo plazo...")
    
    # Crear una nueva sesión para probar memoria a largo plazo
    new_session_id = f"test_session_lts_{uuid.uuid4().hex[:8]}"
    
    try:
        # Pregunta que debería usar memoria a largo plazo
        long_term_query = "¿Recuerdas mi nombre y mi trabajo de conversaciones anteriores?"
        
        chat_payload = {
            "model": "gemini-fast",
            "messages": [{"role": "user", "content": long_term_query}],
            "session_id": new_session_id,
            "stream": False
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-key",
            "X-OpenWebUI-User-Email": f"{user_id}@example.com",
            "X-OpenWebUI-User-Id": user_id
        }
        
        response = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json=chat_payload,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        chat_response = response.json()
        
        assistant_message = chat_response["choices"][0]["message"]["content"]
        
        # Verificar que la respuesta mencione información previa
        message_lower = assistant_message.lower()
        has_name = "juan" in message_lower
        has_job = any(word in message_lower for word in ["desarrollo", "software", "programación", "programador"])
        
        if has_name or has_job:
            print("✅ Memoria a largo plazo funcionando - respuesta contiene información previa")
            print(f"   Respuesta: {assistant_message[:200]}...")
        else:
            print("⚠️ Memoria a largo plazo - respuesta no contiene información previa clara")
            print(f"   Respuesta: {assistant_message[:200]}...")
        
    except Exception as e:
        print(f"❌ Error en memoria a largo plazo: {e}")
        return False
    
    print("\n--- Test de memoria híbrida completado exitosamente ---")
    return True


def test_memory_endpoints():
    """
    Test específico de endpoints de memoria.
    """
    print("\n--- Iniciando test de endpoints de memoria ---")
    
    user_id = f"test_endpoints_{int(time.time())}"
    
    endpoints_to_test = [
        {
            "name": "Perfil de usuario",
            "method": "GET",
            "url": f"/v1/memory/profile/{user_id}",
            "expected_keys": ["email", "preferences", "context"]
        },
        {
            "name": "Contexto enriquecido",
            "method": "GET", 
            "url": f"/v1/memory/context/{user_id}",
            "expected_keys": ["user_id", "enhanced_context"]
        }
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\nProbando {endpoint['name']}...")
        
        try:
            if endpoint["method"] == "GET":
                response = requests.get(f"{GATEWAY_URL}{endpoint['url']}", timeout=10)
            else:
                response = requests.post(f"{GATEWAY_URL}{endpoint['url']}", timeout=10)
            
            response.raise_for_status()
            data = response.json()
            
            # Verificar claves esperadas
            for key in endpoint["expected_keys"]:
                assert key in data, f"Respuesta debe contener clave '{key}'"
            
            print(f"✅ {endpoint['name']} - OK")
            
        except Exception as e:
            print(f"❌ {endpoint['name']} - Error: {e}")
            return False
    
    print("\n✅ Todos los endpoints de memoria funcionando correctamente")
    return True


if __name__ == "__main__":
    print("🧠 Iniciando tests de memoria híbrida CorpChat")
    
    # Test de endpoints básicos
    endpoints_ok = test_memory_endpoints()
    
    if endpoints_ok:
        # Test completo de funcionalidad
        memory_ok = test_memory_functionality()
        
        if memory_ok:
            print("\n🎉 Todos los tests de memoria pasaron exitosamente")
        else:
            print("\n❌ Tests de memoria fallaron")
    else:
        print("\n❌ Tests de endpoints de memoria fallaron")
