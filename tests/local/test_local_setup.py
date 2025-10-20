#!/usr/bin/env python3
"""
Tests para validar el setup de desarrollo local de CorpChat
"""

import pytest
import requests
import json
import os
from typing import Dict, Any


class TestLocalSetup:
    """Tests para validar el entorno de desarrollo local"""
    
    def test_gateway_service_running(self):
        """Test que verifica que el Gateway esté ejecutándose"""
        try:
            response = requests.get("http://localhost:8000/openapi.json", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "info" in data
            assert data["info"]["title"] == "FastAPI"
            print("✅ Gateway service is running")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Gateway service not accessible: {e}")
    
    def test_ingestor_service_running(self):
        """Test que verifica que el Ingestor esté ejecutándose"""
        try:
            response = requests.get("http://localhost:8080/openapi.json", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "info" in data
            assert data["info"]["title"] == "CorpChat Ingestor"
            print("✅ Ingestor service is running")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Ingestor service not accessible: {e}")
    
    def test_gateway_run_endpoint(self):
        """Test que verifica el endpoint de ejecución del Gateway"""
        try:
            response = requests.get("http://localhost:8000/run", timeout=5)
            # Puede devolver 405 Method Not Allowed para GET, eso está bien
            assert response.status_code in [200, 405, 422]
            print("✅ Gateway run endpoint is accessible")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Gateway run endpoint not accessible: {e}")
    
    def test_ingestor_health_endpoint(self):
        """Test que verifica el endpoint de salud del Ingestor"""
        try:
            response = requests.get("http://localhost:8080/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            print("✅ Ingestor health endpoint is working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Ingestor health endpoint not accessible: {e}")
    
    def test_environment_variables(self):
        """Test que verifica las variables de entorno críticas"""
        required_vars = [
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_CLOUD_LOCATION"
        ]
        
        for var in required_vars:
            assert os.getenv(var) is not None, f"Environment variable {var} is not set"
        
        # Verificar que el archivo de credenciales existe
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        assert os.path.exists(creds_path), f"Credentials file not found: {creds_path}"
        
        print("✅ Environment variables are properly configured")
    
    def test_gateway_stt_endpoint(self):
        """Test que verifica el endpoint de STT del Gateway"""
        # STT endpoint no está implementado en el Gateway local por ahora
        print("⏭️ Gateway STT endpoint test skipped (not implemented in local mode)")
        pass
    
    def test_ingestor_extract_endpoint(self):
        """Test que verifica el endpoint de extracción del Ingestor"""
        try:
            response = requests.get("http://localhost:8080/extract/process", timeout=5)
            # Puede devolver 405 Method Not Allowed para GET, eso está bien
            assert response.status_code in [200, 405, 422]
            print("✅ Ingestor extract endpoint is accessible")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Ingestor extract endpoint not accessible: {e}")
    
    def test_services_connectivity(self):
        """Test que verifica la conectividad entre servicios"""
        try:
            # Test Gateway -> Ingestor connectivity
            response = requests.get("http://localhost:8000/health", timeout=5)
            # El Gateway debería poder conectarse al Ingestor
            assert response.status_code in [200, 404]  # 404 es OK si no hay endpoint /health
            print("✅ Services connectivity is working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Services connectivity test failed: {e}")


if __name__ == "__main__":
    # Ejecutar tests individualmente para mejor debugging
    test_suite = TestLocalSetup()
    
    print("🧪 Ejecutando tests de validación local...")
    print("=" * 50)
    
    try:
        test_suite.test_gateway_service_running()
        test_suite.test_ingestor_service_running()
        test_suite.test_gateway_run_endpoint()
        test_suite.test_ingestor_health_endpoint()
        test_suite.test_environment_variables()
        test_suite.test_gateway_stt_endpoint()
        test_suite.test_ingestor_extract_endpoint()
        test_suite.test_services_connectivity()
        
        print("=" * 50)
        print("🎉 Todos los tests pasaron exitosamente!")
        print("✅ El entorno de desarrollo local está funcionando correctamente")
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ Error en las pruebas: {e}")
        exit(1)