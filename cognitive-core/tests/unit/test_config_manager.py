"""
Test simple para validar que el ConfigManager funciona correctamente.
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.config.config_manager import ConfigManager
from src.shared.exceptions import ConfigurationError


def test_config_manager_basic():
    """Test básico del ConfigManager."""
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir)
    
    # Crear configuración básica
    core_config = {
        "core": {
            "name": "TestCore",
            "version": "1.0.0",
            "description": "Test Core"
        },
        "models": {
            "gemini-fast": {
                "display_name": "Gemini Fast",
                "description": "Fast model",
                "llm_model": "gemini-2.0-flash",
                "capabilities": ["text", "reasoning"]
            }
        },
        "orchestrator": {
            "name": "TestOrchestrator"
        },
        "session": {
            "service": "InMemorySessionService"
        },
        "a2a": {
            "enabled": True
        },
        "logging": {
            "level": "INFO"
        }
    }
    
    # Escribir archivo de configuración
    with open(config_dir / "core.yaml", "w") as f:
        yaml.dump(core_config, f)
    
    try:
        # Inicializar ConfigManager
        config_manager = ConfigManager(config_dir)
        
        # Verificar que se inicializó correctamente
        assert config_manager is not None
        
        # Obtener configuración principal
        core_config_obj = config_manager.get_core_config()
        assert core_config_obj.core["name"] == "TestCore"
        assert "gemini-fast" in core_config_obj.models
        
        print("✅ ConfigManager básico funciona correctamente")
        
    except Exception as e:
        print(f"❌ Error en ConfigManager: {e}")
        raise
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)


def test_config_manager_error_handling():
    """Test manejo de errores en ConfigManager."""
    # Test directorio inexistente
    with pytest.raises(ConfigurationError):
        ConfigManager("/path/that/does/not/exist")
    
    print("✅ Manejo de errores funciona correctamente")


if __name__ == "__main__":
    test_config_manager_basic()
    test_config_manager_error_handling()
    print("🎉 Todos los tests básicos pasaron!")