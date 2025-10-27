"""
GPS Fleet Tool para el TerrestrialLogisticsAgent.

Esta herramienta simula el acceso a la flota GPS de Argos con datos realistas
para demostrar la integración con sistemas de seguimiento vehicular.
"""

import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base_tool import BaseTool, FunctionTool
from ...shared.types import ToolConfig, ToolType
from ...shared.exceptions import ToolError
from ...shared.utils import get_logger


class GPSFleetTool(BaseTool):
    """
    Herramienta para acceso a flota GPS de Argos.
    
    Simula el acceso a datos de GPS de la flota de camiones de Argos
    con información realista de ubicación, estado y capacidad.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa la herramienta GPS Fleet.
        
        Args:
            config: Configuración de la herramienta
        """
        tool_config = ToolConfig(
            name="gps_fleet_tool",
            type=ToolType.FUNCTION_TOOL,
            description="Acceso a flota GPS de Argos con seguimiento en tiempo real",
            parameters=config or {}
        )
        super().__init__(tool_config)
        
        self._logger = get_logger(__name__)
        self._fleet_data = self._initialize_fleet_data()
        self._logger.info("GPS Fleet Tool inicializada")
    
    def _initialize_fleet_data(self) -> List[Dict[str, Any]]:
        """
        Inicializa datos simulados de la flota GPS.
        
        Returns:
            Lista con datos de vehículos de la flota
        """
        # Datos realistas basados en el caso Argos
        plants = [
            {"name": "Planta Bogotá", "location": "Bogotá, Colombia", "coordinates": {"lat": 4.6097, "lon": -74.0817}},
            {"name": "Planta Medellín", "location": "Medellín, Colombia", "coordinates": {"lat": 6.2442, "lon": -75.5812}},
            {"name": "Planta Cali", "location": "Cali, Colombia", "coordinates": {"lat": 3.4516, "lon": -76.5320}}
        ]
        
        port_cartagena = {"name": "Puerto Cartagena", "location": "Cartagena, Colombia", "coordinates": {"lat": 10.3910, "lon": -75.4794}}
        
        fleet = []
        
        # Generar flota de 150 camiones (según configuración Argos)
        for i in range(1, 151):
            # Asignar ubicación aleatoria
            if i <= 50:
                current_location = plants[0]  # Bogotá
            elif i <= 100:
                current_location = plants[1]  # Medellín
            else:
                current_location = plants[2]  # Cali
            
            # Estado del vehículo
            status_options = ["available", "in_transit", "loading", "unloading", "maintenance"]
            status = random.choice(status_options)
            
            # Capacidad del camión (toneladas)
            capacity = random.choice([800, 1000, 1200])  # Capacidades realistas
            
            # Tiempo estimado de llegada si está en tránsito
            eta = None
            if status == "in_transit":
                eta = (datetime.now() + timedelta(hours=random.randint(1, 8))).isoformat()
            
            vehicle = {
                "vehicle_id": f"ARGOS-{i:03d}",
                "driver_name": f"Conductor {i}",
                "current_location": current_location,
                "status": status,
                "capacity_tonnes": capacity,
                "current_load": random.randint(0, capacity) if status in ["loading", "in_transit"] else 0,
                "destination": port_cartagena if status == "in_transit" else None,
                "eta": eta,
                "fuel_level": random.randint(20, 100),
                "last_update": datetime.now().isoformat(),
                "route_optimization_score": random.uniform(0.7, 1.0)
            }
            
            fleet.append(vehicle)
        
        return fleet
    
    def execute(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta consulta a la flota GPS.
        
        Args:
            input_data: Datos de entrada con parámetros de consulta
            context: Contexto adicional (opcional)
            
        Returns:
            Resultado de la consulta GPS
            
        Raises:
            ToolError: Si hay error ejecutando la consulta
        """
        try:
            query_type = input_data.get("query_type", "get_fleet_status")
            
            if query_type == "get_fleet_status":
                return self._get_fleet_status(input_data)
            elif query_type == "get_available_vehicles":
                return self._get_available_vehicles(input_data)
            elif query_type == "get_vehicle_location":
                return self._get_vehicle_location(input_data)
            elif query_type == "optimize_fleet_assignment":
                return self._optimize_fleet_assignment(input_data)
            else:
                raise ToolError(f"Tipo de consulta no soportado: {query_type}")
                
        except Exception as e:
            raise ToolError(f"Error ejecutando consulta GPS: {e}")
    
    def _get_fleet_status(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene estado general de la flota.
        
        Args:
            input_data: Parámetros de consulta
            
        Returns:
            Estado de la flota
        """
        # Filtrar por ubicación si se especifica
        location_filter = input_data.get("location")
        filtered_fleet = self._fleet_data
        
        if location_filter:
            filtered_fleet = [
                vehicle for vehicle in self._fleet_data
                if location_filter.lower() in vehicle["current_location"]["name"].lower()
            ]
        
        # Estadísticas de la flota
        total_vehicles = len(filtered_fleet)
        available = len([v for v in filtered_fleet if v["status"] == "available"])
        in_transit = len([v for v in filtered_fleet if v["status"] == "in_transit"])
        loading = len([v for v in filtered_fleet if v["status"] == "loading"])
        maintenance = len([v for v in filtered_fleet if v["status"] == "maintenance"])
        
        # Capacidad total disponible
        total_capacity = sum(v["capacity_tonnes"] for v in filtered_fleet if v["status"] == "available")
        
        return {
            "query_type": "fleet_status",
            "timestamp": datetime.now().isoformat(),
            "fleet_summary": {
                "total_vehicles": total_vehicles,
                "available": available,
                "in_transit": in_transit,
                "loading": loading,
                "maintenance": maintenance,
                "total_available_capacity": total_capacity
            },
            "location_filter": location_filter,
            "vehicles": filtered_fleet[:10] if len(filtered_fleet) > 10 else filtered_fleet  # Limitar respuesta
        }
    
    def _get_available_vehicles(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene vehículos disponibles para asignación.
        
        Args:
            input_data: Parámetros de consulta
            
        Returns:
            Lista de vehículos disponibles
        """
        required_capacity = input_data.get("required_capacity", 0)
        preferred_location = input_data.get("preferred_location")
        
        # Filtrar vehículos disponibles
        available_vehicles = [
            vehicle for vehicle in self._fleet_data
            if vehicle["status"] == "available" and vehicle["capacity_tonnes"] >= required_capacity
        ]
        
        # Ordenar por proximidad si se especifica ubicación preferida
        if preferred_location:
            available_vehicles.sort(
                key=lambda v: self._calculate_distance_score(v["current_location"], preferred_location),
                reverse=True
            )
        
        # Limitar número de resultados
        max_results = input_data.get("max_results", 20)
        available_vehicles = available_vehicles[:max_results]
        
        return {
            "query_type": "available_vehicles",
            "timestamp": datetime.now().isoformat(),
            "required_capacity": required_capacity,
            "preferred_location": preferred_location,
            "available_count": len(available_vehicles),
            "vehicles": available_vehicles
        }
    
    def _get_vehicle_location(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene ubicación específica de un vehículo.
        
        Args:
            input_data: Parámetros de consulta
            
        Returns:
            Ubicación del vehículo
        """
        vehicle_id = input_data.get("vehicle_id")
        
        if not vehicle_id:
            raise ToolError("vehicle_id es requerido para consulta de ubicación")
        
        # Buscar vehículo
        vehicle = next((v for v in self._fleet_data if v["vehicle_id"] == vehicle_id), None)
        
        if not vehicle:
            raise ToolError(f"Vehículo no encontrado: {vehicle_id}")
        
        return {
            "query_type": "vehicle_location",
            "timestamp": datetime.now().isoformat(),
            "vehicle_id": vehicle_id,
            "location": vehicle["current_location"],
            "status": vehicle["status"],
            "eta": vehicle["eta"],
            "last_update": vehicle["last_update"]
        }
    
    def _optimize_fleet_assignment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimiza asignación de flota para una carga específica.
        
        Args:
            input_data: Parámetros de optimización
            
        Returns:
            Asignación optimizada de flota
        """
        cargo_weight = input_data.get("cargo_weight", 0)
        origin_location = input_data.get("origin_location")
        destination_location = input_data.get("destination_location")
        
        if cargo_weight <= 0:
            raise ToolError("cargo_weight debe ser mayor que 0")
        
        # Calcular número de camiones necesarios
        trucks_needed = []
        remaining_weight = cargo_weight
        
        # Obtener vehículos disponibles ordenados por capacidad
        available_vehicles = [
            v for v in self._fleet_data
            if v["status"] == "available"
        ]
        available_vehicles.sort(key=lambda v: v["capacity_tonnes"], reverse=True)
        
        # Asignar camiones
        for vehicle in available_vehicles:
            if remaining_weight <= 0:
                break
            
            assigned_weight = min(remaining_weight, vehicle["capacity_tonnes"])
            trucks_needed.append({
                "vehicle_id": vehicle["vehicle_id"],
                "driver_name": vehicle["driver_name"],
                "capacity": vehicle["capacity_tonnes"],
                "assigned_weight": assigned_weight,
                "current_location": vehicle["current_location"],
                "route_score": vehicle["route_optimization_score"]
            })
            
            remaining_weight -= assigned_weight
        
        # Calcular métricas de optimización
        total_assigned_capacity = sum(t["assigned_weight"] for t in trucks_needed)
        efficiency_score = (total_assigned_capacity / cargo_weight) * 100 if cargo_weight > 0 else 0
        
        return {
            "query_type": "fleet_optimization",
            "timestamp": datetime.now().isoformat(),
            "cargo_weight": cargo_weight,
            "origin_location": origin_location,
            "destination_location": destination_location,
            "trucks_needed": len(trucks_needed),
            "total_assigned_capacity": total_assigned_capacity,
            "efficiency_score": round(efficiency_score, 2),
            "assignment": trucks_needed,
            "remaining_weight": max(0, remaining_weight)
        }
    
    def _calculate_distance_score(self, location1: Dict[str, Any], location2: str) -> float:
        """
        Calcula score de distancia entre ubicaciones (simulado).
        
        Args:
            location1: Primera ubicación
            location2: Segunda ubicación (string)
            
        Returns:
            Score de proximidad (0-1)
        """
        # Simulación simple de proximidad
        location_names = ["bogotá", "medellín", "cali", "cartagena"]
        
        loc1_name = location1["name"].lower()
        loc2_name = location2.lower()
        
        if loc1_name == loc2_name:
            return 1.0
        
        # Score basado en proximidad geográfica simulada
        proximity_scores = {
            ("bogotá", "medellín"): 0.8,
            ("bogotá", "cali"): 0.6,
            ("bogotá", "cartagena"): 0.4,
            ("medellín", "cali"): 0.7,
            ("medellín", "cartagena"): 0.5,
            ("cali", "cartagena"): 0.6
        }
        
        key = tuple(sorted([loc1_name, loc2_name]))
        return proximity_scores.get(key, 0.3)


def create_gps_fleet_tool() -> FunctionTool:
    """
    Crea una instancia de GPS Fleet Tool como FunctionTool.
    
    Returns:
        FunctionTool configurada para GPS Fleet
    """
    gps_tool = GPSFleetTool()
    
    def gps_fleet_function(query_type: str = "get_fleet_status", **kwargs) -> Dict[str, Any]:
        """
        Función wrapper para GPS Fleet Tool.
        
        Args:
            query_type: Tipo de consulta GPS
            **kwargs: Parámetros adicionales
            
        Returns:
            Resultado de la consulta GPS
        """
        input_data = {"query_type": query_type, **kwargs}
        return gps_tool.execute(input_data)
    
    # Configurar FunctionTool
    tool_config = ToolConfig(
        name="gps_fleet_tool",
        type=ToolType.FUNCTION_TOOL,
        description="Acceso a flota GPS de Argos con seguimiento en tiempo real"
    )
    
    return FunctionTool(gps_fleet_function, tool_config)
