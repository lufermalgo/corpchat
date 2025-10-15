"""
Configuración compartida de pytest para tests del ingestor.

Define fixtures y configuraciones globales.
"""

import pytest
import logging


# Configurar logging para tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@pytest.fixture(scope="session")
def test_config():
    """Configuración global de tests."""
    return {
        "chunk_size": 512,
        "overlap": 128,
        "embedding_dims": 768,
        "test_timeout": 30
    }


@pytest.fixture
def sample_pdf_content():
    """Contenido de ejemplo para PDF."""
    return """
# Manual de Usuario

## Introducción

Este es un manual de usuario de ejemplo para probar la extracción de PDF.

## Sección 1: Instalación

Para instalar el software:
1. Descarga el instalador
2. Ejecuta el archivo .exe
3. Sigue las instrucciones en pantalla

## Sección 2: Configuración

La configuración inicial requiere:
- Nombre de usuario
- Correo electrónico
- Contraseña segura

| Parámetro | Valor por Defecto | Requerido |
|-----------|-------------------|-----------|
| Timeout   | 30s               | No        |
| Max Retry | 3                 | No        |
| Debug     | False             | No        |
"""


@pytest.fixture
def sample_table_data():
    """Tabla de ejemplo para tests."""
    return {
        "headers": ["ID", "Nombre", "Departamento", "Salario"],
        "rows": [
            ["001", "Juan Pérez", "Ventas", "$50,000"],
            ["002", "María García", "Marketing", "$55,000"],
            ["003", "Pedro López", "IT", "$60,000"],
            ["004", "Ana Martínez", "RRHH", "$52,000"],
            ["005", "Carlos Rodríguez", "Finanzas", "$58,000"]
        ]
    }


def pytest_configure(config):
    """Configuración inicial de pytest."""
    config.addinivalue_line(
        "markers", "slow: marca tests que son lentos"
    )
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "requires_gcp: marca tests que requieren GCP configurado"
    )
    config.addinivalue_line(
        "markers", "requires_tesseract: marca tests que requieren Tesseract instalado"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica items de test según markers."""
    import os
    
    # Skip tests que requieren Tesseract si no está instalado
    skip_tesseract = pytest.mark.skip(reason="Tesseract no instalado")
    
    # Skip tests que requieren GCP si no está configurado
    skip_gcp = pytest.mark.skip(reason="GCP no configurado")
    has_gcp = os.getenv("GOOGLE_CLOUD_PROJECT") is not None
    
    for item in items:
        if "requires_tesseract" in item.keywords:
            try:
                import pytesseract
                pytesseract.get_tesseract_version()
            except:
                item.add_marker(skip_tesseract)
        
        if "requires_gcp" in item.keywords and not has_gcp:
            item.add_marker(skip_gcp)

