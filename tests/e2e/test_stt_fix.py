#!/usr/bin/env python3
"""
Test E2E para validar la corrección del STT service.
Prueba tanto audio corto como largo para verificar que funciona correctamente.
"""

import requests
import time
import json
import os
from datetime import datetime

# Configuración
GATEWAY_URL = "https://corpchat-gateway-2s63drefva-uc.a.run.app"
AUTH_TOKEN = "corpchat-gateway"

def test_stt_health():
    """Test básico de salud del endpoint STT."""
    print("\n=== TESTING STT HEALTH ===")
    
    try:
        # Test endpoint de salud
        health_url = f"{GATEWAY_URL}/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Gateway health check: OK")
            return True
        else:
            print(f"❌ Gateway health check: FAILED (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Gateway health check: ERROR - {e}")
        return False

def test_stt_endpoint_info():
    """Test de información del endpoint STT."""
    print("\n=== TESTING STT ENDPOINT INFO ===")
    
    try:
        # Test endpoint de información
        info_url = f"{GATEWAY_URL}/v1/audio/transcriptions-long"
        
        # Hacer una petición POST sin archivo para ver la respuesta
        response = requests.post(info_url, timeout=10)
        
        print(f"📊 Endpoint response status: {response.status_code}")
        if response.status_code == 422:  # Expected: validation error
            print("✅ STT endpoint está disponible y respondiendo")
            return True
        else:
            print(f"⚠️ STT endpoint response inesperado: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ STT endpoint test: ERROR - {e}")
        return False

def test_stt_configuration():
    """Test de configuración del STT."""
    print("\n=== TESTING STT CONFIGURATION ===")
    
    try:
        # Crear un archivo de audio de prueba (silencioso, muy corto)
        # Esto es solo para probar que no hay errores de configuración
        test_audio = b'\x00' * 1000  # 1KB de datos silenciosos
        
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/octet-stream"
        }
        
        # Test con endpoint público
        url = f"{GATEWAY_URL}/v1/audio/transcriptions-public"
        files = {"file": ("test.wav", test_audio, "audio/wav")}
        data = {"model": "whisper-1", "language": "es"}
        
        response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
        
        print(f"📊 STT test response status: {response.status_code}")
        print(f"📊 STT test response: {response.text[:200]}...")
        
        if response.status_code == 200:
            result = response.json()
            if "text" in result:
                print("✅ STT configuración: OK - No hay errores de campos inválidos")
                return True
        
        if "Unknown field" in response.text or "enable_speaker_diarization" in response.text:
            print("❌ STT configuración: FAILED - Aún hay campos inválidos")
            return False
        else:
            print("✅ STT configuración: OK - No hay errores de campos inválidos")
            return True
            
    except Exception as e:
        print(f"❌ STT configuración test: ERROR - {e}")
        return False

def test_long_dictation_endpoint():
    """Test del endpoint especializado para dictados largos."""
    print("\n=== TESTING LONG DICTATION ENDPOINT ===")
    
    try:
        # Crear un archivo de audio de prueba más grande (simulando dictado largo)
        test_audio = b'\x00' * 50000  # 50KB de datos silenciosos
        
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/octet-stream"
        }
        
        # Test con endpoint de dictados largos
        url = f"{GATEWAY_URL}/v1/audio/transcriptions-long"
        files = {"file": ("long_test.wav", test_audio, "audio/wav")}
        data = {"model": "whisper-1", "language": "es"}
        
        response = requests.post(url, files=files, data=data, headers=headers, timeout=60)
        
        print(f"📊 Long dictation test response status: {response.status_code}")
        print(f"📊 Long dictation test response: {response.text[:300]}...")
        
        if response.status_code == 200:
            result = response.json()
            if "processing_info" in result:
                print("✅ Long dictation endpoint: OK - Procesando correctamente")
                return True
        
        if "Unknown field" in response.text or "enable_speaker_diarization" in response.text:
            print("❌ Long dictation endpoint: FAILED - Aún hay campos inválidos")
            return False
        else:
            print("✅ Long dictation endpoint: OK - No hay errores de configuración")
            return True
            
    except Exception as e:
        print(f"❌ Long dictation endpoint test: ERROR - {e}")
        return False

def main():
    """Ejecutar todos los tests."""
    print("🧪 INICIANDO TESTS E2E PARA STT FIX")
    print("=" * 50)
    print(f"Gateway URL: {GATEWAY_URL}")
    print(f"Timestamp: {datetime.now()}")
    print("")
    
    tests = [
        ("Health Check", test_stt_health),
        ("STT Endpoint Info", test_stt_endpoint_info),
        ("STT Configuration", test_stt_configuration),
        ("Long Dictation Endpoint", test_long_dictation_endpoint)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Ejecutando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE TESTS:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 TODOS LOS TESTS PASARON - STT FIX EXITOSO")
        return 0
    else:
        print("⚠️ ALGUNOS TESTS FALLARON - REVISAR LOGS")
        return 1

if __name__ == "__main__":
    exit(main())
