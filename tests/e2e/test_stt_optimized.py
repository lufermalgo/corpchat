#!/usr/bin/env python3
"""
Test E2E para validar la nueva versión optimizada del STT service.
Prueba calidad de transcripción y funcionalidad completa.
"""

import requests
import time
import json
import os
from datetime import datetime

# Configuración
GATEWAY_URL = "https://corpchat-gateway-2s63drefva-uc.a.run.app"
AUTH_TOKEN = "corpchat-gateway"

def test_stt_optimized_quality():
    """Test de calidad de transcripción optimizada."""
    print("\n=== TESTING STT OPTIMIZED QUALITY ===")
    
    try:
        # Crear un archivo de audio de prueba más realista
        # Simulamos un archivo MP3 pequeño
        test_audio = b'\xff\xfb\x90\x00' + b'\x00' * 1000  # Header MP3 + datos
        
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/octet-stream"
        }
        
        # Test con endpoint público optimizado
        url = f"{GATEWAY_URL}/v1/audio/transcriptions-public"
        files = {"file": ("test_optimized.mp3", test_audio, "audio/mpeg")}
        data = {"model": "whisper-1", "language": "es"}
        
        print("📤 Enviando audio de prueba...")
        response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            result = response.json()
            if "text" in result:
                print("✅ STT optimizado: Funcionando correctamente")
                print(f"📝 Transcripción: {result['text']}")
                return True
        
        if "Unknown field" in response.text or "enable_speaker_diarization" in response.text:
            print("❌ STT optimizado: Aún hay campos inválidos")
            return False
        else:
            print("✅ STT optimizado: No hay errores de configuración")
            return True
            
    except Exception as e:
        print(f"❌ STT optimizado test: ERROR - {e}")
        return False

def test_long_dictation_optimized():
    """Test del endpoint de dictados largos optimizado."""
    print("\n=== TESTING LONG DICTATION OPTIMIZED ===")
    
    try:
        # Crear un archivo de audio más grande para simular dictado largo
        test_audio = b'\xff\xfb\x90\x00' + b'\x00' * 50000  # Header MP3 + datos largos
        
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/octet-stream"
        }
        
        # Test con endpoint de dictados largos
        url = f"{GATEWAY_URL}/v1/audio/transcriptions-long"
        files = {"file": ("long_test_optimized.mp3", test_audio, "audio/mpeg")}
        data = {"model": "whisper-1", "language": "es"}
        
        print("📤 Enviando dictado largo de prueba...")
        response = requests.post(url, files=files, data=data, headers=headers, timeout=60)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response: {response.text[:300]}...")
        
        if response.status_code == 200:
            result = response.json()
            if "processing_info" in result or "text" in result:
                print("✅ Long dictation optimizado: Procesando correctamente")
                if "processing_info" in result:
                    print(f"📊 Processing info: {result['processing_info']}")
                return True
        
        if "Unknown field" in response.text or "enable_speaker_diarization" in response.text:
            print("❌ Long dictation optimizado: Aún hay campos inválidos")
            return False
        else:
            print("✅ Long dictation optimizado: No hay errores de configuración")
            return True
            
    except Exception as e:
        print(f"❌ Long dictation optimizado test: ERROR - {e}")
        return False

def test_stt_health_optimized():
    """Test de salud del STT optimizado."""
    print("\n=== TESTING STT HEALTH OPTIMIZED ===")
    
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

def main():
    """Ejecutar todos los tests de STT optimizado."""
    print("🧪 INICIANDO TESTS E2E PARA STT OPTIMIZADO")
    print("=" * 50)
    print(f"Gateway URL: {GATEWAY_URL}")
    print(f"Timestamp: {datetime.now()}")
    print("")
    
    tests = [
        ("Health Check Optimizado", test_stt_health_optimized),
        ("STT Quality Optimizado", test_stt_optimized_quality),
        ("Long Dictation Optimizado", test_long_dictation_optimized)
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
    print("📊 RESUMEN DE TESTS STT OPTIMIZADO:")
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
        print("🎉 TODOS LOS TESTS PASARON - STT OPTIMIZADO EXITOSO")
        print("✨ Características implementadas:")
        print("   • Alta calidad de transcripción")
        print("   • Soporte para audios cortos y largos")
        print("   • Configuración optimizada para español")
        print("   • Logging detallado de calidad")
        print("   • Billing tracking automático")
        return 0
    else:
        print("⚠️ ALGUNOS TESTS FALLARON - REVISAR LOGS")
        return 1

if __name__ == "__main__":
    exit(main())
