#!/usr/bin/env python3
"""
Test E2E para Streaming - Verificar que las respuestas se envían en tiempo real
"""

import requests
import time
import json
from typing import List, Dict

# Configuración
GATEWAY_URL = "https://corpchat-gateway-2s63drefva-uc.a.run.app"
TEST_MESSAGE = "Cuenta hasta 10, número por número, con una explicación breve de cada número."
EXPECTED_MIN_CHUNKS = 10  # Esperamos al menos 10 chunks
MAX_FIRST_TOKEN_LATENCY = 0.5  # 500ms máximo para primer token


def test_streaming_latency():
    """Test 1: Verificar latencia del primer token."""
    print("🧪 Test 1: Verificando latencia del primer token")
    
    payload = {
        "model": "gemini-fast",
        "messages": [{"role": "user", "content": TEST_MESSAGE}],
        "stream": True
    }
    
    try:
        start_time = time.time()
        first_chunk_time = None
        
        with requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=30
        ) as response:
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    
                    if line_str.startswith('data: ') and line_str != 'data: [DONE]':
                        if first_chunk_time is None:
                            first_chunk_time = time.time()
                            latency = first_chunk_time - start_time
                            
                            print(f"✅ Primer token recibido en: {latency:.3f}s")
                            
                            if latency <= MAX_FIRST_TOKEN_LATENCY:
                                print(f"✅ Latencia OK: {latency:.3f}s <= {MAX_FIRST_TOKEN_LATENCY}s")
                                return True
                            else:
                                print(f"❌ Latencia alta: {latency:.3f}s > {MAX_FIRST_TOKEN_LATENCY}s")
                                return False
                        
                        # Parsear chunk para verificar formato
                        try:
                            data_str = line_str[6:]  # Remover 'data: '
                            chunk_data = json.loads(data_str)
                            
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    print(f"📝 Chunk: {content[:50]}...")
                                    
                        except json.JSONDecodeError:
                            continue
        
        if first_chunk_time is None:
            print("❌ No se recibió ningún chunk")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de latencia: {e}")
        return False


def test_streaming_format():
    """Test 2: Verificar formato SSE correcto."""
    print("\n🧪 Test 2: Verificando formato SSE")
    
    payload = {
        "model": "gemini-fast",
        "messages": [{"role": "user", "content": "Responde con exactamente 3 palabras."}],
        "stream": True
    }
    
    try:
        chunks_received = 0
        total_content = ""
        
        with requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=30
        ) as response:
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    
                    if line_str.startswith('data: '):
                        if line_str == 'data: [DONE]':
                            print("✅ Chunk final [DONE] recibido")
                            break
                        
                        # Parsear chunk
                        try:
                            data_str = line_str[6:]  # Remover 'data: '
                            chunk_data = json.loads(data_str)
                            
                            # Verificar estructura del chunk
                            required_fields = ['id', 'object', 'created', 'model', 'choices']
                            for field in required_fields:
                                if field not in chunk_data:
                                    print(f"❌ Campo faltante en chunk: {field}")
                                    return False
                            
                            # Verificar choices
                            if len(chunk_data['choices']) > 0:
                                choice = chunk_data['choices'][0]
                                if 'delta' in choice:
                                    delta = choice['delta']
                                    if 'content' in delta:
                                        chunks_received += 1
                                        total_content += delta['content']
                                        print(f"✅ Chunk {chunks_received}: {delta['content'][:30]}...")
                                    
                        except json.JSONDecodeError as e:
                            print(f"❌ Error parseando chunk: {e}")
                            return False
        
        print(f"✅ Total chunks recibidos: {chunks_received}")
        print(f"✅ Contenido completo: {total_content}")
        
        return chunks_received > 0 and total_content.strip() != ""
        
    except Exception as e:
        print(f"❌ Error en test de formato: {e}")
        return False


def test_streaming_throughput():
    """Test 3: Verificar throughput de streaming."""
    print("\n🧪 Test 3: Verificando throughput de streaming")
    
    payload = {
        "model": "gemini-fast",
        "messages": [{"role": "user", "content": "Escribe un párrafo de 100 palabras sobre inteligencia artificial."}],
        "stream": True
    }
    
    try:
        start_time = time.time()
        chunks_received = 0
        total_content = ""
        
        with requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=60
        ) as response:
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    
                    if line_str.startswith('data: ') and line_str != 'data: [DONE]':
                        try:
                            data_str = line_str[6:]
                            chunk_data = json.loads(data_str)
                            
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    chunks_received += 1
                                    total_content += delta['content']
                                    
                        except json.JSONDecodeError:
                            continue
                    elif line_str == 'data: [DONE]':
                        break
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calcular throughput aproximado (caracteres por segundo)
        chars_per_second = len(total_content) / duration if duration > 0 else 0
        
        print(f"✅ Duración total: {duration:.2f}s")
        print(f"✅ Chunks recibidos: {chunks_received}")
        print(f"✅ Caracteres totales: {len(total_content)}")
        print(f"✅ Throughput: {chars_per_second:.1f} chars/s")
        
        # Verificar throughput mínimo (aproximadamente 10 tokens/s = ~40 chars/s)
        min_throughput = 20  # chars/s mínimo
        if chars_per_second >= min_throughput:
            print(f"✅ Throughput OK: {chars_per_second:.1f} >= {min_throughput} chars/s")
            return True
        else:
            print(f"❌ Throughput bajo: {chars_per_second:.1f} < {min_throughput} chars/s")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de throughput: {e}")
        return False


def test_streaming_error_handling():
    """Test 4: Verificar manejo de errores en streaming."""
    print("\n🧪 Test 4: Verificando manejo de errores")
    
    # Test con modelo inválido
    payload = {
        "model": "modelo-inexistente",
        "messages": [{"role": "user", "content": "Hola"}],
        "stream": True
    }
    
    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=10
        )
        
        if response.status_code == 400:
            print("✅ Error 400 manejado correctamente para modelo inválido")
            return True
        else:
            print(f"❌ Código de estado inesperado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de manejo de errores: {e}")
        return False


def main():
    """Ejecutar todos los tests de streaming."""
    print("🚀 CorpChat Streaming - E2E Tests")
    print("=" * 50)
    
    tests = [
        ("Latencia Primer Token", test_streaming_latency),
        ("Formato SSE", test_streaming_format),
        ("Throughput", test_streaming_throughput),
        ("Manejo de Errores", test_streaming_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Ejecutando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE TESTS DE STREAMING")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} tests pasaron")
    
    if passed == len(results):
        print("🎉 ¡Todos los tests de streaming pasaron!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Verificar que Open WebUI muestre streaming en la UI")
        print("2. Probar con diferentes modelos Gemini")
        print("3. Validar streaming con archivos adjuntos")
        print("4. Monitorear métricas de latencia en producción")
    else:
        print("⚠️ Algunos tests fallaron. Revisar implementación de streaming.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
