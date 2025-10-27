"""
Test de integración básico para componentes del Core Cognitivo.

Valida que los componentes base funcionen correctamente en conjunto
antes de continuar con la implementación completa.
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.config.config_manager import ConfigManager
from src.config.validator import ConfigValidator
from src.agents.terrestrial_agent import TerrestrialLogisticsAgent
from src.shared.types import AgentConfig, AgentSkill, ToolConfig, AgentType, ToolType
from src.shared.exceptions import ConfigurationError, AgentError


class TestIntegration:
    """Tests de integración para componentes base."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
        # Crear estructura de directorios
        (self.config_dir / "agents").mkdir()
        (self.config_dir / "argos").mkdir()
        
        # Crear configuración completa
        self._create_test_configurations()
    
    def teardown_method(self):
        """Cleanup después de cada test."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_configurations(self):
        """Crear configuraciones de prueba."""
        # Configuración principal
        core_config = {
            "core": {
                "name": "CognitiveCore",
                "version": "1.0.0",
                "description": "Core Cognitivo Universal"
            },
            "models": {
                "gemini-fast": {
                    "display_name": "Gemini-Fast",
                    "description": "Respuestas rápidas y eficientes",
                    "llm_model": "gemini-2.0-flash",
                    "capabilities": ["text", "reasoning"]
                },
                "gemini-pro": {
                    "display_name": "Gemini-Pro",
                    "description": "Análisis profundo y estratégico",
                    "llm_model": "gemini-2.0-flash",
                    "capabilities": ["text", "reasoning", "analysis"]
                }
            },
            "orchestrator": {
                "name": "CognitiveOrchestrator",
                "description": "Coordina multi-agent workflows",
                "default_model": "gemini-fast",
                "capabilities": ["orchestration", "routing", "memory"]
            },
            "session": {
                "service": "InMemorySessionService",
                "runner": "InMemoryRunner",
                "app_name": "cognitive-core"
            },
            "a2a": {
                "enabled": True,
                "task_timeout": 300,
                "max_retries": 3
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        with open(self.config_dir / "core.yaml", "w") as f:
            yaml.dump(core_config, f)
        
        # Configuración de agente terrestre
        terrestrial_config = {
            "agent": {
                "name": "TerrestrialLogisticsAgent",
                "type": "LlmAgent",
                "model": "gemini-fast",
                "enabled": True
            },
            "skills": [
                {
                    "id": "plan_terrestrial_transport",
                    "name": "Plan Terrestrial Transport",
                    "description": "Planifica transporte terrestre desde plantas hasta puerto",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "destination": {"type": "string"},
                            "cargo_weight": {"type": "number"},
                            "cargo_type": {"type": "string"}
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "trucks_needed": {"type": "integer"},
                            "route": {"type": "string"},
                            "estimated_cost": {"type": "number"},
                            "estimated_time": {"type": "string"}
                        }
                    }
                },
                {
                    "id": "gps_fleet_optimization",
                    "name": "GPS Fleet Optimization",
                    "description": "Optimiza flota GPS disponible",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "fleet_size": {"type": "integer"},
                            "current_locations": {"type": "array"}
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "optimized_assignment": {"type": "array"},
                            "efficiency_score": {"type": "number"}
                        }
                    }
                }
            ],
            "tools": [
                {
                    "name": "gps_fleet_tool",
                    "type": "FunctionTool",
                    "description": "Acceso a flota GPS de Argos"
                },
                {
                    "name": "route_optimizer_tool",
                    "type": "FunctionTool",
                    "description": "Optimización de rutas terrestres"
                },
                {
                    "name": "geofence_tool",
                    "type": "FunctionTool",
                    "description": "Monitoreo de geocercas"
                }
            ],
            "argos_specific": {
                "gps_coverage": "100%",
                "fleet_size": 150,
                "plants": [
                    {"name": "Planta Bogotá", "location": "Bogotá, Colombia", "capacity": 5000},
                    {"name": "Planta Medellín", "location": "Medellín, Colombia", "capacity": 3000},
                    {"name": "Planta Cali", "location": "Cali, Colombia", "capacity": 4000}
                ],
                "ports": [
                    {"name": "Puerto Cartagena", "location": "Cartagena, Colombia", "capacity": 10000}
                ]
            }
        }
        
        with open(self.config_dir / "agents" / "terrestrial.yaml", "w") as f:
            yaml.dump(terrestrial_config, f)
        
        # Configuración del caso Argos
        argos_config = {
            "case": {
                "name": "Argos Multimodal Logistics",
                "description": "Caso de validación: Integración transporte terrestre-marítimo",
                "client": "Argos",
                "domain": "Logistics"
            },
            "scenario": {
                "name": "8000 toneladas a Alabama",
                "description": "Envío de 8000 toneladas de cemento desde plantas colombianas hasta Alabama, USA",
                "cargo": {
                    "type": "cement",
                    "weight": 8000,
                    "destination": "Alabama, USA",
                    "delivery_date": "2024-12-15"
                },
                "flow": {
                    "phase_1": "Plantas colombianas → Puerto Cartagena (terrestre)",
                    "phase_2": "Puerto Cartagena → Mobile, Alabama (marítimo)",
                    "phase_3": "Mobile, Alabama → Destino final (terrestre local)"
                }
            },
            "validation": {
                "success_criteria": [
                    "Plan terrestre detallado con rutas y camiones",
                    "Plan marítimo con embarcación y tiempos",
                    "Plan multimodal integrado",
                    "Costos estimados para cada fase",
                    "Tiempos estimados totales",
                    "Identificación de cuellos de botella"
                ],
                "expected_outputs": {
                    "terrestrial": {
                        "trucks_needed": "8-10 camiones",
                        "route": "Plantas → Puerto Cartagena",
                        "cost_range": "$8,000 - $12,000",
                        "time_range": "2-3 días"
                    },
                    "maritime": {
                        "vessel": "MV Argos Carrier",
                        "route": "Cartagena → Mobile, Alabama",
                        "cost_range": "$35,000 - $40,000",
                        "time_range": "8-10 días"
                    },
                    "multimodal": {
                        "total_cost": "$43,000 - $52,000",
                        "total_time": "10-13 días",
                        "efficiency_score": "> 85%"
                    }
                }
            },
            "test_data": {
                "plants": [
                    {"name": "Planta Bogotá", "location": "Bogotá, Colombia", "capacity": 5000, "available": 3000},
                    {"name": "Planta Medellín", "location": "Medellín, Colombia", "capacity": 3000, "available": 2000},
                    {"name": "Planta Cali", "location": "Cali, Colombia", "capacity": 4000, "available": 3000}
                ],
                "trucks": {
                    "total_fleet": 150,
                    "available": 120,
                    "capacity_per_truck": 1000
                },
                "vessels": [
                    {
                        "name": "MV Argos Carrier",
                        "capacity": 8000,
                        "route": "Cartagena - Mobile, Alabama",
                        "next_departure": "2024-11-20",
                        "cost_per_ton": 4.5
                    }
                ],
                "ports": {
                    "cartagena": {
                        "name": "Puerto Cartagena",
                        "country": "Colombia",
                        "capacity": 15000,
                        "loading_time": "2 días"
                    },
                    "mobile": {
                        "name": "Mobile, Alabama",
                        "country": "USA",
                        "capacity": 20000,
                        "unloading_time": "1 día"
                    }
                }
            }
        }
        
        with open(self.config_dir / "argos" / "argos_case.yaml", "w") as f:
            yaml.dump(argos_config, f)
    
    def test_config_manager_integration(self):
        """Test integración completa del ConfigManager."""
        # Inicializar ConfigManager
        config_manager = ConfigManager(self.config_dir)
        
        # Validar configuración principal
        core_config = config_manager.get_core_config()
        assert core_config.core["name"] == "CognitiveCore"
        assert len(core_config.models) == 2
        assert "gemini-fast" in core_config.models
        assert "gemini-pro" in core_config.models
        
        # Validar configuración de agente
        agent_config = config_manager.get_agent_config("terrestrial")
        assert agent_config.name == "TerrestrialLogisticsAgent"
        assert agent_config.type.value == "LlmAgent"
        assert len(agent_config.skills) == 2
        assert len(agent_config.tools) == 3
        
        # Validar configuración del caso Argos
        argos_config = config_manager.get_argos_case_config()
        assert argos_config.case["name"] == "Argos Multimodal Logistics"
        assert argos_config.scenario["cargo"]["weight"] == 8000
        
        # Validar configuración completa
        validator = ConfigValidator(config_manager)
        validation_result = validator.validate_all()
        assert validation_result is True
    
    def test_terrestrial_agent_integration(self):
        """Test integración del TerrestrialLogisticsAgent."""
        # Obtener configuración del agente
        config_manager = ConfigManager(self.config_dir)
        agent_config = config_manager.get_agent_config("terrestrial")
        
        # Crear agente
        agent = TerrestrialLogisticsAgent(agent_config)
        
        # Validar inicialización
        assert agent.name == "TerrestrialLogisticsAgent"
        assert agent.enabled is True
        assert len(agent.skills) == 2
        assert len(agent.tools) == 3
        
        # Validar configuración
        validation_result = agent.validate_configuration()
        assert validation_result is True
        
        # Test procesamiento de consulta básica
        result = agent.process_query("¿Cuál es el estado de la flota GPS?")
        
        assert result["agent"] == "TerrestrialLogisticsAgent"
        assert result["query_type"] == "fleet_status"
        assert "analysis" in result
        assert "confidence" in result
        assert result["confidence"] > 0
        
        # Test ejecución de skill
        skill_result = agent.execute_skill("plan_terrestrial_transport", {
            "destination": "Puerto Cartagena",
            "cargo_weight": 1000,
            "cargo_type": "cement"
        })
        
        assert skill_result["skill_id"] == "plan_terrestrial_transport"
        assert skill_result["destination"] == "Puerto Cartagena"
        assert skill_result["cargo_weight"] == 1000
        assert "trucks_needed" in skill_result
        assert "estimated_total_cost" in skill_result
    
    def test_end_to_end_basic_flow(self):
        """Test flujo básico end-to-end."""
        # 1. Cargar configuración
        config_manager = ConfigManager(self.config_dir)
        validator = ConfigValidator(config_manager)
        
        # Validar configuración
        assert validator.validate_all() is True
        
        # 2. Crear agente terrestre
        agent_config = config_manager.get_agent_config("terrestrial")
        agent = TerrestrialLogisticsAgent(agent_config)
        
        # 3. Simular consulta del caso Argos
        query = "Necesito enviar 8000 toneladas de cemento desde las plantas hasta Puerto Cartagena"
        
        # 4. Procesar consulta
        result = agent.process_query(query)
        
        # 5. Validar resultado
        assert result["agent"] == "TerrestrialLogisticsAgent"
        assert result["query_type"] in ["transport_planning", "fleet_status"]
        assert "analysis" in result
        assert "confidence" in result
        assert result["confidence"] > 80
        
        # 6. Ejecutar skill específico
        skill_result = agent.execute_skill("plan_terrestrial_transport", {
            "destination": "Puerto Cartagena",
            "cargo_weight": 8000,
            "cargo_type": "cement"
        })
        
        # 7. Validar skill result
        assert skill_result["skill_id"] == "plan_terrestrial_transport"
        assert skill_result["cargo_weight"] == 8000
        assert skill_result["trucks_needed"] > 0
        assert skill_result["estimated_total_cost"] > 0
        assert skill_result["estimated_total_time"] > 0
        
        # 8. Validar que el resultado es realista para el caso Argos
        # Debería necesitar aproximadamente 8-10 camiones para 8000 toneladas
        assert 5 <= skill_result["trucks_needed"] <= 15
        
        # El costo debería estar en el rango esperado ($8,000 - $12,000)
        assert 5000 <= skill_result["estimated_total_cost"] <= 15000
    
    def test_error_handling_integration(self):
        """Test manejo de errores en integración."""
        # Test configuración inválida
        invalid_config_dir = Path("/invalid/path")
        with pytest.raises(ConfigurationError):
            ConfigManager(invalid_config_dir)
        
        # Test agente con configuración inválida
        invalid_agent_config = AgentConfig(
            name="",  # Nombre vacío - inválido
            type=AgentType.LLM_AGENT,
            model="gemini-fast",
            enabled=True,
            skills=[],
            tools=[]
        )
        
        with pytest.raises(AgentError):
            TerrestrialLogisticsAgent(invalid_agent_config)
    
    def test_performance_basic(self):
        """Test básico de performance."""
        import time
        
        # Cargar configuración
        start_time = time.time()
        config_manager = ConfigManager(self.config_dir)
        config_load_time = time.time() - start_time
        
        # Crear agente
        start_time = time.time()
        agent_config = config_manager.get_agent_config("terrestrial")
        agent = TerrestrialLogisticsAgent(agent_config)
        agent_creation_time = time.time() - start_time
        
        # Procesar consulta
        start_time = time.time()
        result = agent.process_query("Estado de la flota GPS")
        query_processing_time = time.time() - start_time
        
        # Validar tiempos (deberían ser rápidos para componentes base)
        assert config_load_time < 1.0  # Menos de 1 segundo
        assert agent_creation_time < 2.0  # Menos de 2 segundos
        assert query_processing_time < 5.0  # Menos de 5 segundos
        
        # Validar que el resultado es válido
        assert result["confidence"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
