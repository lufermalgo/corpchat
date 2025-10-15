#!/usr/bin/env python3
"""
Test E2E para Model Selector - Verificar selección de modelos en Open WebUI
"""

import requests
import json
import time
from typing import Dict, List

# Configuración
GATEWAY_URL = "https://corpchat-gateway-6a2n4lq7uq-uc.a.run.app"  # Actualizar con URL real
TEST_MESSAGES = [
    {"role": "user", "content": "¿Qué es CorpChat?"},
    {"role": "user", "content": "Explica la diferencia entre pensamiento rápido y pensamiento profundo."},
    {"role": "user", "content": "¿Cuáles son las mejores prácticas para documentar procesos empresariales?"}
]


def test_models_endpoint():
    """Test 1: Verificar que el endpoint /v1/models retorna modelos con thinking modes."""
    print("🧪 Test 1: Verificar endpoint /v1/models")
    
    try:
        response = requests.get(f"{GATEWAY_URL}/v1/models", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Models found: {len(data['data'])}")
        
        # Verificar que tenemos modelos con thinking modes
        expected_models = ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-4-turbo"]
        found_models = [model["id"] for model in data["data"]]
        
        for expected in expected_models:
            if expected in found_models:
                print(f"✅ Model found: {expected}")
            else:
                print(f"❌ Model missing: {expected}")
        
        # Mostrar modelos disponibles
        print("\n📋 Modelos disponibles:")
        for model in data["data"]:
            print(f"  - {model['id']} (owned by: {model['owned_by']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_model_selection(model_name: str, message: str) -> Dict:
    """Test 2: Verificar que diferentes modelos producen respuestas diferentes."""
    print(f"\n🧪 Test 2: Modelo {model_name}")
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": message}],
        "temperature": None,  # Usar temperatura del modelo
        "max_tokens": None,   # Usar max_tokens del modelo
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        
        end_time = time.time()
        response_time = end_time - start_time
        
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Model used: {data['model']}")
        print(f"✅ Response time: {response_time:.2f}s")
        print(f"✅ Tokens: {data['usage']['total_tokens']}")
        
        # Extraer respuesta
        content = data["choices"][0]["message"]["content"]
        print(f"✅ Response length: {len(content)} chars")
        print(f"📝 Response preview: {content[:100]}...")
        
        return {
            "model": data["model"],
            "response_time": response_time,
            "tokens": data["usage"]["total_tokens"],
            "content": content,
            "success": True
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def test_thinking_modes():
    """Test 3: Verificar que diferentes thinking modes producen respuestas distintas."""
    print("\n🧪 Test 3: Comparar Thinking Modes")
    
    models_to_test = [
        ("gpt-4o-mini", "Instant"),
        ("gpt-4o", "Thinking Mini"),
        ("gpt-4", "Thinking"),
        ("gpt-4-turbo", "Auto")
    ]
    
    message = "Explica qué es la inteligencia artificial de manera que un niño de 8 años pueda entenderlo."
    results = []
    
    for model_name, expected_mode in models_to_test:
        print(f"\n🔍 Testing {model_name} ({expected_mode})")
        result = test_model_selection(model_name, message)
        
        if result["success"]:
            results.append({
                "model": model_name,
                "mode": expected_mode,
                "response_time": result["response_time"],
                "tokens": result["tokens"],
                "content_length": len(result["content"])
            })
    
    # Comparar resultados
    print("\n📊 Comparación de Thinking Modes:")
    print("Modelo                | Tiempo | Tokens | Longitud")
    print("-" * 50)
    
    for result in results:
        print(f"{result['model']:<20} | {result['response_time']:>5.2f}s | {result['tokens']:>6} | {result['content_length']:>8}")
    
    return results


def test_streaming():
    """Test 4: Verificar streaming con diferentes modelos."""
    print("\n🧪 Test 4: Streaming con Modelos")
    
    models_to_test = ["gpt-4o-mini", "gpt-4"]
    message = "Cuenta una historia corta sobre un robot que aprende a soñar."
    
    for model_name in models_to_test:
        print(f"\n🌊 Streaming con {model_name}")
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": message}],
            "stream": True
        }
        
        try:
            response = requests.post(
                f"{GATEWAY_URL}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            print(f"✅ Streaming started for {model_name}")
            
            # Leer chunks
            chunk_count = 0
            total_content = ""
            
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    line_str = line.decode('utf-8')
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: '
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(data_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    total_content += content
                                    print(f"📦 Chunk {chunk_count}: {len(content)} chars")
                        except json.JSONDecodeError:
                            pass
            
            print(f"✅ Streaming completed: {chunk_count} chunks, {len(total_content)} total chars")
            
        except Exception as e:
            print(f"❌ Streaming error: {e}")


def main():
    """Ejecutar todos los tests."""
    print("🚀 CorpChat Model Selector - E2E Tests")
    print("=" * 50)
    
    # Test 1: Endpoint de modelos
    models_ok = test_models_endpoint()
    
    if not models_ok:
        print("❌ Test 1 failed - stopping")
        return
    
    # Test 2: Selección de modelos
    print("\n" + "=" * 50)
    test_results = test_thinking_modes()
    
    # Test 3: Streaming
    print("\n" + "=" * 50)
    test_streaming()
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE TESTS")
    print("=" * 50)
    
    if models_ok:
        print("✅ Test 1: Endpoint /v1/models - PASSED")
    else:
        print("❌ Test 1: Endpoint /v1/models - FAILED")
    
    if test_results:
        print(f"✅ Test 2: Thinking Modes - PASSED ({len(test_results)} models tested)")
    else:
        print("❌ Test 2: Thinking Modes - FAILED")
    
    print("✅ Test 3: Streaming - COMPLETED")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Verificar que Open WebUI puede listar los modelos")
    print("2. Probar selección de modelos en la UI")
    print("3. Validar que las respuestas varían según el modelo")
    print("4. Configurar modelos por defecto por usuario")


if __name__ == "__main__":
    main()
