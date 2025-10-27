"""
Tests unitarios para TerrestrialLogisticsAgent.

Valida la funcionalidad básica del agente terrestre y su integración
con las herramientas especializadas.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.terrestrial_agent import TerrestrialLogisticsAgent
from src.shared.types import AgentConfig, AgentSkill, ToolConfig, AgentType, ToolType
from src.shared.exceptions import AgentError


class TestTerrestrialLogisticsAgent:
    """Tests para TerrestrialLogisticsAgent."""
    
    def setup_method(self):
        """Setup para cada test."""
        # Crear configuración de agente para testing
        self.agent_config = AgentConfig(
            name="TestTerrestrialAgent",
            type=AgentType.LLM_AGENT,
            model="gemini-fast",
            enabled=True,
            skills=[
                AgentSkill(
                    id="plan_terrestrial_transport",
                    name="Plan Terrestrial Transport",
                    description="Planifica transporte terrestre",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"}
                ),
                AgentSkill(
                    id="gps_fleet_optimization",
                    name="GPS Fleet Optimization",
                    description="Optimiza flota GPS",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"}
                )
            ],
            tools=[
                ToolConfig(
                    name="gps_fleet_tool",
                    type=ToolType.FUNCTION_TOOL,
                    description="GPS Fleet Tool"
                ),
                ToolConfig(
                    name="route_optimizer_tool",
                    type=ToolType.FUNCTION_TOOL,
                    description="Route Optimizer Tool"
                ),
                ToolConfig(
                    name="geofence_tool",
                    type=ToolType.FUNCTION_TOOL,
                    description="Geofence Tool"
                )
            ]
        )
        
        self.agent = TerrestrialLogisticsAgent(self.agent_config)
    
    def test_agent_initialization(self):
        """Test inicialización del agente."""
        assert self.agent.name == "TestTerrestrialAgent"
        assert self.agent.agent_type == AgentType.LLM_AGENT
        assert self.agent.model == "gemini-fast"
        assert self.agent.enabled is True
        assert len(self.agent.skills) == 2
        assert len(self.agent.tools) == 3
    
    def test_agent_properties(self):
        """Test propiedades del agente."""
        assert self.agent.has_skill("plan_terrestrial_transport") is True
        assert self.agent.has_skill("gps_fleet_optimization") is True
        assert self.agent.has_skill("invalid_skill") is False
        
        assert self.agent.has_tool("gps_fleet_tool") is True
        assert self.agent.has_tool("route_optimizer_tool") is True
        assert self.agent.has_tool("invalid_tool") is False
    
    def test_get_skill_by_id(self):
        """Test obtención de skill por ID."""
        skill = self.agent.get_skill_by_id("plan_terrestrial_transport")
        assert skill is not None
        assert skill.name == "Plan Terrestrial Transport"
        
        skill = self.agent.get_skill_by_id("invalid_skill")
        assert skill is None
    
    def test_get_tool_by_name(self):
        """Test obtención de tool por nombre."""
        tool = self.agent.get_tool_by_name("gps_fleet_tool")
        assert tool is not None
        assert tool.description == "GPS Fleet Tool"
        
        tool = self.agent.get_tool_by_name("invalid_tool")
        assert tool is None
    
    def test_enable_disable_agent(self):
        """Test habilitar/deshabilitar agente."""
        assert self.agent.enabled is True
        
        self.agent.disable()
        assert self.agent.enabled is False
        
        self.agent.enable()
        assert self.agent.enabled is True
    
    def test_validate_configuration(self):
        """Test validación de configuración."""
        result = self.agent.validate_configuration()
        assert result is True
    
    def test_validate_skills(self):
        """Test validación de skills."""
        result = self.agent.validate_skills()
        assert result is True
    
    def test_validate_tools(self):
        """Test validación de tools."""
        result = self.agent.validate_tools()
        assert result is True
    
    def test_get_agent_info(self):
        """Test obtención de información del agente."""
        info = self.agent.get_agent_info()
        
        assert info["name"] == "TestTerrestrialAgent"
        assert info["type"] == "LlmAgent"
        assert info["model"] == "gemini-fast"
        assert info["enabled"] is True
        assert info["skills_count"] == 2
        assert info["tools_count"] == 3
    
    def test_get_skills_info(self):
        """Test obtención de información de skills."""
        skills_info = self.agent.get_skills_info()
        
        assert len(skills_info) == 2
        assert skills_info[0]["id"] == "plan_terrestrial_transport"
        assert skills_info[1]["id"] == "gps_fleet_optimization"
    
    def test_get_tools_info(self):
        """Test obtención de información de tools."""
        tools_info = self.agent.get_tools_info()
        
        assert len(tools_info) == 3
        tool_names = [tool["name"] for tool in tools_info]
        assert "gps_fleet_tool" in tool_names
        assert "route_optimizer_tool" in tool_names
        assert "geofence_tool" in tool_names
    
    @patch('src.agents.terrestrial_agent.create_gps_fleet_tool')
    @patch('src.agents.terrestrial_agent.create_route_optimizer_tool')
    @patch('src.agents.terrestrial_agent.create_geofence_tool')
    def test_process_query_fleet_status(self, mock_geofence, mock_route, mock_gps):
        """Test procesamiento de consulta de estado de flota."""
        # Mock de herramientas
        mock_gps_tool = MagicMock()
        mock_gps_tool.run.return_value = {
            "fleet_summary": {
                "total_vehicles": 150,
                "available": 120,
                "in_transit": 20,
                "loading": 8,
                "maintenance": 2
            }
        }
        mock_gps.return_value = mock_gps_tool
        
        mock_route_tool = MagicMock()
        mock_route.return_value = mock_route_tool
        
        mock_geofence_tool = MagicMock()
        mock_geofence.return_value = mock_geofence_tool
        
        # Crear nuevo agente con mocks
        agent = TerrestrialLogisticsAgent(self.agent_config)
        
        # Test consulta de estado de flota
        result = agent.process_query("¿Cuál es el estado de la flota GPS?")
        
        assert result["agent"] == "TestTerrestrialAgent"
        assert result["query_type"] == "fleet_status"
        assert "analysis" in result
        assert "confidence" in result
        assert result["confidence"] > 0
    
    @patch('src.agents.terrestrial_agent.create_gps_fleet_tool')
    @patch('src.agents.terrestrial_agent.create_route_optimizer_tool')
    @patch('src.agents.terrestrial_agent.create_geofence_tool')
    def test_process_query_route_optimization(self, mock_geofence, mock_route, mock_gps):
        """Test procesamiento de consulta de optimización de rutas."""
        # Mock de herramientas
        mock_gps_tool = MagicMock()
        mock_gps.return_value = mock_gps_tool
        
        mock_route_tool = MagicMock()
        mock_route_tool.run.return_value = {
            "optimal_route": {
                "route_type": "highway",
                "distance_km": 650,
                "estimated_time_hours": 8.1,
                "estimated_cost_usd": 97.5,
                "efficiency_score": 0.85
            },
            "all_options": [],
            "recommendation": "Ruta recomendada por autopista"
        }
        mock_route.return_value = mock_route_tool
        
        mock_geofence_tool = MagicMock()
        mock_geofence.return_value = mock_geofence_tool
        
        # Crear nuevo agente con mocks
        agent = TerrestrialLogisticsAgent(self.agent_config)
        
        # Test consulta de optimización de rutas
        result = agent.process_query("Optimiza la ruta de Bogotá a Cartagena para 1000 toneladas")
        
        assert result["agent"] == "TestTerrestrialAgent"
        assert result["query_type"] == "route_optimization"
        assert "analysis" in result
        assert "confidence" in result
    
    @patch('src.agents.terrestrial_agent.create_gps_fleet_tool')
    @patch('src.agents.terrestrial_agent.create_route_optimizer_tool')
    @patch('src.agents.terrestrial_agent.create_geofence_tool')
    def test_execute_skill_plan_terrestrial_transport(self, mock_geofence, mock_route, mock_gps):
        """Test ejecución de skill de planificación terrestre."""
        # Mock de herramientas
        mock_gps_tool = MagicMock()
        mock_gps_tool.run.return_value = {
            "assignment": [
                {
                    "vehicle_id": "ARGOS-001",
                    "assigned_weight": 1000,
                    "current_location": {"name": "Planta Bogotá"}
                }
            ],
            "trucks_needed": 1,
            "total_assigned_capacity": 1000,
            "efficiency_score": 95
        }
        mock_gps.return_value = mock_gps_tool
        
        mock_route_tool = MagicMock()
        mock_route_tool.run.return_value = {
            "optimal_route": {
                "estimated_cost_usd": 97.5,
                "estimated_time_hours": 8.1
            }
        }
        mock_route.return_value = mock_route_tool
        
        mock_geofence_tool = MagicMock()
        mock_geofence.return_value = mock_geofence_tool
        
        # Crear nuevo agente con mocks
        agent = TerrestrialLogisticsAgent(self.agent_config)
        
        # Test ejecución de skill
        result = agent.execute_skill("plan_terrestrial_transport", {
            "destination": "Puerto Cartagena",
            "cargo_weight": 1000,
            "cargo_type": "cement"
        })
        
        assert result["skill_id"] == "plan_terrestrial_transport"
        assert result["destination"] == "Puerto Cartagena"
        assert result["cargo_weight"] == 1000
        assert result["trucks_needed"] == 1
        assert "estimated_total_cost" in result
        assert "estimated_total_time" in result
    
    def test_analyze_query_type(self):
        """Test análisis de tipo de consulta."""
        # Test diferentes tipos de consulta
        assert self.agent._analyze_query_type("¿Cuál es el estado de la flota?") == "fleet_status"
        assert self.agent._analyze_query_type("Optimiza la ruta de Bogotá a Cartagena") == "route_optimization"
        assert self.agent._analyze_query_type("¿Hay alertas de geocercas?") == "geofence_monitoring"
        assert self.agent._analyze_query_type("Planifica el envío de 1000 toneladas") == "transport_planning"
        assert self.agent._analyze_query_type("Consulta general") == "general"
    
    def test_extract_location_from_query(self):
        """Test extracción de ubicación de consulta."""
        assert self.agent._extract_location_from_query("Estado de flota en Bogotá") == "Bogotá"
        assert self.agent._extract_location_from_query("Vehículos en Medellín") == "Medellín"
        assert self.agent._extract_location_from_query("Flota en Cali") == "Cali"
        assert self.agent._extract_location_from_query("Consulta sin ubicación") is None
    
    def test_extract_route_parameters(self):
        """Test extracción de parámetros de ruta."""
        origin, destination, cargo_weight = self.agent._extract_route_parameters(
            "Optimiza ruta de Bogotá a Cartagena para 2000 toneladas"
        )
        
        assert origin == "bogota"
        assert destination == "cartagena"
        assert cargo_weight == 2000
    
    def test_extract_transport_parameters(self):
        """Test extracción de parámetros de transporte."""
        cargo_weight, destination = self.agent._extract_transport_parameters(
            "Planifica envío de 5000 toneladas a Alabama"
        )
        
        assert cargo_weight == 5000
        assert destination == "Alabama, USA"
    
    def test_agent_string_representation(self):
        """Test representación string del agente."""
        str_repr = str(self.agent)
        assert "TerrestrialLogisticsAgent" in str_repr
        assert "TestTerrestrialAgent" in str_repr
        
        repr_str = repr(self.agent)
        assert "TerrestrialLogisticsAgent" in repr_str
        assert "TestTerrestrialAgent" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
