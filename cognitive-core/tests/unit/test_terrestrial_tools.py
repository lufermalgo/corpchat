"""
Tests unitarios para herramientas terrestres.

Valida la funcionalidad de GPS Fleet Tool, Route Optimizer Tool y Geofence Tool.
"""

import pytest
from unittest.mock import patch

from src.tools.terrestrial.gps_fleet_tool import GPSFleetTool, create_gps_fleet_tool
from src.tools.terrestrial.route_optimizer_tool import RouteOptimizerTool, create_route_optimizer_tool
from src.tools.terrestrial.geofence_tool import GeofenceTool, create_geofence_tool
from src.shared.exceptions import ToolError


class TestGPSFleetTool:
    """Tests para GPS Fleet Tool."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.gps_tool = GPSFleetTool()
    
    def test_gps_tool_initialization(self):
        """Test inicialización de GPS Fleet Tool."""
        assert self.gps_tool.name == "gps_fleet_tool"
        assert self.gps_tool.tool_type.value == "FunctionTool"
        assert len(self.gps_tool._fleet_data) == 150  # Flota completa de Argos
    
    def test_get_fleet_status(self):
        """Test obtención de estado de flota."""
        result = self.gps_tool.execute({
            "query_type": "get_fleet_status"
        })
        
        assert result["query_type"] == "fleet_status"
        assert "fleet_summary" in result
        assert "total_vehicles" in result["fleet_summary"]
        assert result["fleet_summary"]["total_vehicles"] == 150
    
    def test_get_fleet_status_with_location_filter(self):
        """Test estado de flota con filtro de ubicación."""
        result = self.gps_tool.execute({
            "query_type": "get_fleet_status",
            "location": "Bogotá"
        })
        
        assert result["query_type"] == "fleet_status"
        assert result["location_filter"] == "Bogotá"
        assert len(result["vehicles"]) <= 50  # Máximo vehículos en Bogotá
    
    def test_get_available_vehicles(self):
        """Test obtención de vehículos disponibles."""
        result = self.gps_tool.execute({
            "query_type": "get_available_vehicles",
            "required_capacity": 1000
        })
        
        assert result["query_type"] == "available_vehicles"
        assert "vehicles" in result
        assert "available_count" in result
        
        # Verificar que todos los vehículos disponibles tienen capacidad suficiente
        for vehicle in result["vehicles"]:
            assert vehicle["capacity_tonnes"] >= 1000
    
    def test_optimize_fleet_assignment(self):
        """Test optimización de asignación de flota."""
        result = self.gps_tool.execute({
            "query_type": "optimize_fleet_assignment",
            "cargo_weight": 5000
        })
        
        assert result["query_type"] == "fleet_optimization"
        assert "assignment" in result
        assert "efficiency_score" in result
        assert result["cargo_weight"] == 5000
        
        # Verificar que la asignación es eficiente
        total_assigned = sum(truck["assigned_weight"] for truck in result["assignment"])
        assert total_assigned >= 5000
    
    def test_get_vehicle_location(self):
        """Test obtención de ubicación de vehículo específico."""
        result = self.gps_tool.execute({
            "query_type": "get_vehicle_location",
            "vehicle_id": "ARGOS-001"
        })
        
        assert result["query_type"] == "vehicle_location"
        assert result["vehicle_id"] == "ARGOS-001"
        assert "location" in result
        assert "status" in result
    
    def test_get_vehicle_location_invalid_id(self):
        """Test ubicación de vehículo con ID inválido."""
        with pytest.raises(ToolError):
            self.gps_tool.execute({
                "query_type": "get_vehicle_location",
                "vehicle_id": "INVALID-ID"
            })
    
    def test_create_gps_fleet_tool_function(self):
        """Test creación de FunctionTool para GPS Fleet."""
        function_tool = create_gps_fleet_tool()
        
        assert function_tool.name == "gps_fleet_tool"
        assert function_tool.tool_type.value == "FunctionTool"
        
        # Test ejecución de función
        result = function_tool.run({"query_type": "get_fleet_status"})
        assert "fleet_summary" in result


class TestRouteOptimizerTool:
    """Tests para Route Optimizer Tool."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.route_tool = RouteOptimizerTool()
    
    def test_route_tool_initialization(self):
        """Test inicialización de Route Optimizer Tool."""
        assert self.route_tool.name == "route_optimizer_tool"
        assert self.route_tool.tool_type.value == "FunctionTool"
        assert "locations" in self.route_tool._route_data
        assert "distances" in self.route_tool._route_data
    
    def test_optimize_route(self):
        """Test optimización de ruta."""
        result = self.route_tool.execute({
            "query_type": "optimize_route",
            "origin": "bogota",
            "destination": "cartagena",
            "cargo_weight": 1000
        })
        
        assert result["query_type"] == "route_optimization"
        assert "optimal_route" in result
        assert "all_options" in result
        assert result["origin"] == "Planta Bogotá"
        assert result["destination"] == "Puerto Cartagena"
        
        optimal_route = result["optimal_route"]
        assert "distance_km" in optimal_route
        assert "estimated_time_hours" in optimal_route
        assert "estimated_cost_usd" in optimal_route
    
    def test_calculate_distance(self):
        """Test cálculo de distancia."""
        result = self.route_tool.execute({
            "query_type": "calculate_distance",
            "origin": "bogota",
            "destination": "medellin"
        })
        
        assert result["query_type"] == "distance_calculation"
        assert "distance_km" in result
        assert result["distance_km"] > 0
        assert result["distance_miles"] > 0
    
    def test_estimate_cost(self):
        """Test estimación de costo."""
        result = self.route_tool.execute({
            "query_type": "estimate_cost",
            "origin": "bogota",
            "destination": "cartagena",
            "cargo_weight": 2000,
            "route_type": "highway"
        })
        
        assert result["query_type"] == "cost_estimation"
        assert "total_cost_usd" in result
        assert "cost_breakdown" in result
        assert result["total_cost_usd"] > 0
        assert result["cargo_weight"] == 2000
    
    def test_estimate_time(self):
        """Test estimación de tiempo."""
        result = self.route_tool.execute({
            "query_type": "estimate_time",
            "origin": "bogota",
            "destination": "cartagena",
            "route_type": "highway"
        })
        
        assert result["query_type"] == "time_estimation"
        assert "driving_time_hours" in result
        assert "total_time_hours" in result
        assert "departure_time" in result
        assert "estimated_arrival" in result
        assert result["total_time_hours"] > result["driving_time_hours"]
    
    def test_compare_routes(self):
        """Test comparación de rutas."""
        result = self.route_tool.execute({
            "query_type": "compare_routes",
            "origin": "bogota",
            "destination": "cartagena",
            "cargo_weight": 1000
        })
        
        assert result["query_type"] == "route_comparison"
        assert "routes" in result
        assert "best_options" in result
        assert len(result["routes"]) > 0
        
        best_options = result["best_options"]
        assert "lowest_cost" in best_options
        assert "fastest" in best_options
        assert "most_efficient" in best_options
    
    def test_optimize_route_invalid_locations(self):
        """Test optimización con ubicaciones inválidas."""
        with pytest.raises(ToolError):
            self.route_tool.execute({
                "query_type": "optimize_route",
                "origin": "invalid_location",
                "destination": "cartagena"
            })
    
    def test_create_route_optimizer_tool_function(self):
        """Test creación de FunctionTool para Route Optimizer."""
        function_tool = create_route_optimizer_tool()
        
        assert function_tool.name == "route_optimizer_tool"
        assert function_tool.tool_type.value == "FunctionTool"
        
        # Test ejecución de función
        result = function_tool.run({
            "query_type": "calculate_distance",
            "origin": "bogota",
            "destination": "medellin"
        })
        assert "distance_km" in result


class TestGeofenceTool:
    """Tests para Geofence Tool."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.geofence_tool = GeofenceTool()
    
    def test_geofence_tool_initialization(self):
        """Test inicialización de Geofence Tool."""
        assert self.geofence_tool.name == "geofence_tool"
        assert self.geofence_tool.tool_type.value == "FunctionTool"
        assert "geofences" in self.geofence_tool._geofence_data
        assert "active_alerts" in self.geofence_tool._geofence_data
    
    def test_get_geofence_status(self):
        """Test obtención de estado de geocercas."""
        result = self.geofence_tool.execute({
            "query_type": "get_geofence_status"
        })
        
        assert result["query_type"] == "geofence_status"
        assert "summary" in result
        assert "geofences" in result
        assert result["summary"]["total_geofences"] > 0
    
    def test_get_geofence_status_with_filters(self):
        """Test estado de geocercas con filtros."""
        result = self.geofence_tool.execute({
            "query_type": "get_geofence_status",
            "type": "plant",
            "priority": "high"
        })
        
        assert result["query_type"] == "geofence_status"
        assert result["filters"]["type"] == "plant"
        assert result["filters"]["priority"] == "high"
        
        # Verificar que todas las geocercas son plantas
        for geofence in result["geofences"]:
            assert geofence["type"] == "plant"
            assert geofence["priority"] == "high"
    
    def test_check_vehicle_location(self):
        """Test verificación de ubicación de vehículo."""
        result = self.geofence_tool.execute({
            "query_type": "check_vehicle_location",
            "vehicle_id": "ARGOS-001",
            "vehicle_location": {"lat": 4.6097, "lon": -74.0817}  # Bogotá
        })
        
        assert result["query_type"] == "vehicle_location_check"
        assert result["vehicle_id"] == "ARGOS-001"
        assert "inside_geofences" in result
        assert "nearby_geofences" in result
        assert "status" in result
    
    def test_get_active_alerts(self):
        """Test obtención de alertas activas."""
        result = self.geofence_tool.execute({
            "query_type": "get_active_alerts"
        })
        
        assert result["query_type"] == "active_alerts"
        assert "statistics" in result
        assert "alerts" in result
    
    def test_create_geofence(self):
        """Test creación de nueva geocerca."""
        result = self.geofence_tool.execute({
            "query_type": "create_geofence",
            "name": "Test Geofence",
            "center": {"lat": 5.0, "lon": -75.0},
            "radius_km": 1.0,
            "priority": "medium"
        })
        
        assert result["query_type"] == "geofence_creation"
        assert "geofence_id" in result
        assert result["geofence"]["name"] == "Test Geofence"
        assert result["geofence"]["priority"] == "medium"
    
    def test_simulate_vehicle_movement(self):
        """Test simulación de movimiento de vehículo."""
        result = self.geofence_tool.execute({
            "query_type": "simulate_vehicle_movement",
            "vehicle_id": "ARGOS-SIM",
            "start_location": {"lat": 4.6097, "lon": -74.0817},  # Bogotá
            "end_location": {"lat": 10.3910, "lon": -75.4794},  # Cartagena
            "duration_hours": 1.0
        })
        
        assert result["query_type"] == "vehicle_movement_simulation"
        assert result["vehicle_id"] == "ARGOS-SIM"
        assert "alerts_generated" in result
        assert "simulation_completed" in result
        assert result["simulation_completed"] is True
    
    def test_create_geofence_tool_function(self):
        """Test creación de FunctionTool para Geofence."""
        function_tool = create_geofence_tool()
        
        assert function_tool.name == "geofence_tool"
        assert function_tool.tool_type.value == "FunctionTool"
        
        # Test ejecución de función
        result = function_tool.run({"query_type": "get_geofence_status"})
        assert "summary" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
