"""
Maritime Partner Tool para el MaritimeLogisticsAgent.

Esta herramienta simula el acceso a socios marítimos de Argos con datos realistas
para demostrar la integración con servicios de transporte marítimo.
"""

import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base_tool import BaseTool, FunctionTool
from ...shared.types import ToolConfig, ToolType
from ...shared.exceptions import ToolError
from ...shared.utils import get_logger


class MaritimePartnerTool(BaseTool):
    """
    Herramienta para acceso a socios marítimos de Argos.
    
    Simula la integración con servicios de transporte marítimo, incluyendo:
    - Selección de buques disponibles
    - Coordinación con puertos
    - Cálculo de fletes
    - Análisis de tiempos de estadía
    """
    
    def __init__(self):
        super().__init__(
            name="maritime_partner_tool",
            description="Herramienta para acceso a socios marítimos de Argos",
            tool_type=ToolType.FUNCTION_TOOL,
            config=ToolConfig(
                name="maritime_partner_tool",
                type=ToolType.FUNCTION_TOOL,
                description="Herramienta para acceso a socios marítimos de Argos",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query_type": {
                            "type": "string",
                            "enum": [
                                "get_available_vessels",
                                "get_port_schedules", 
                                "calculate_freight",
                                "analyze_lay_time",
                                "get_maritime_routes",
                                "check_vessel_capacity"
                            ],
                            "description": "Tipo de consulta a realizar"
                        },
                        "origin_port": {
                            "type": "string",
                            "description": "Puerto de origen"
                        },
                        "destination_port": {
                            "type": "string", 
                            "description": "Puerto de destino"
                        },
                        "cargo_weight": {
                            "type": "number",
                            "description": "Peso de la carga en toneladas"
                        },
                        "departure_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Fecha de salida deseada"
                        }
                    },
                    "required": ["query_type"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "query_type": {"type": "string"},
                        "result": {"type": "object"},
                        "timestamp": {"type": "string"}
                    }
                }
            )
        )
        self.logger = get_logger(f"Tool.{self.name}")
        
        # Datos simulados de socios marítimos
        self._maritime_data = {
            "vessels": [
                {
                    "vessel_id": "MV_ARGOS_CARRIER",
                    "name": "MV Argos Carrier",
                    "capacity_tonnes": 8000,
                    "current_location": "Puerto Cartagena",
                    "next_departure": "2024-11-20",
                    "route": "Cartagena - Mobile, Alabama",
                    "cost_per_ton": 4.5,
                    "transit_time_days": 8,
                    "status": "available"
                },
                {
                    "vessel_id": "MV_CEMENT_EXPRESS",
                    "name": "MV Cement Express", 
                    "capacity_tonnes": 12000,
                    "current_location": "Puerto Barranquilla",
                    "next_departure": "2024-11-25",
                    "route": "Barranquilla - Mobile, Alabama",
                    "cost_per_ton": 4.2,
                    "transit_time_days": 9,
                    "status": "available"
                },
                {
                    "vessel_id": "MV_LOGISTICS_PRO",
                    "name": "MV Logistics Pro",
                    "capacity_tonnes": 15000,
                    "current_location": "Puerto Buenaventura",
                    "next_departure": "2024-12-01",
                    "route": "Buenaventura - Mobile, Alabama",
                    "cost_per_ton": 4.8,
                    "transit_time_days": 12,
                    "status": "maintenance"
                }
            ],
            "ports": {
                "cartagena": {
                    "name": "Puerto Cartagena",
                    "country": "Colombia",
                    "capacity": 15000,
                    "loading_rate_tonnes_per_day": 2000,
                    "unloading_rate_tonnes_per_day": 2500,
                    "lay_time_hours": 48,
                    "facilities": ["cement_silo", "bulk_loading", "container_terminal"]
                },
                "mobile": {
                    "name": "Mobile, Alabama",
                    "country": "USA",
                    "capacity": 20000,
                    "loading_rate_tonnes_per_day": 3000,
                    "unloading_rate_tonnes_per_day": 3500,
                    "lay_time_hours": 36,
                    "facilities": ["bulk_unloading", "cement_silo", "rail_connection"]
                },
                "barranquilla": {
                    "name": "Puerto Barranquilla",
                    "country": "Colombia", 
                    "capacity": 12000,
                    "loading_rate_tonnes_per_day": 1500,
                    "unloading_rate_tonnes_per_day": 1800,
                    "lay_time_hours": 60,
                    "facilities": ["bulk_loading", "container_terminal"]
                }
            },
            "routes": {
                "cartagena_mobile": {
                    "origin": "Puerto Cartagena",
                    "destination": "Mobile, Alabama",
                    "distance_nm": 1200,
                    "transit_time_days": 8,
                    "weather_factor": 1.1,
                    "fuel_cost_per_ton": 0.8
                },
                "barranquilla_mobile": {
                    "origin": "Puerto Barranquilla", 
                    "destination": "Mobile, Alabama",
                    "distance_nm": 1350,
                    "transit_time_days": 9,
                    "weather_factor": 1.2,
                    "fuel_cost_per_ton": 0.9
                }
            }
        }
    
    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una consulta específica a los socios marítimos.
        
        Args:
            query: Diccionario con los parámetros de la consulta
            
        Returns:
            Diccionario con el resultado de la consulta
        """
        query_type = query.get("query_type")
        self.logger.info(f"Ejecutando consulta marítima: {query_type}")
        
        try:
            if query_type == "get_available_vessels":
                return self._get_available_vessels(query)
            elif query_type == "get_port_schedules":
                return self._get_port_schedules(query)
            elif query_type == "calculate_freight":
                return self._calculate_freight(query)
            elif query_type == "analyze_lay_time":
                return self._analyze_lay_time(query)
            elif query_type == "get_maritime_routes":
                return self._get_maritime_routes(query)
            elif query_type == "check_vessel_capacity":
                return self._check_vessel_capacity(query)
            else:
                raise ToolError(f"Tipo de consulta no soportado: {query_type}")
                
        except Exception as e:
            self.logger.error(f"Error ejecutando consulta marítima: {e}")
            raise ToolError(f"Error en consulta marítima: {e}")
    
    def _get_available_vessels(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene buques disponibles para una ruta específica."""
        origin_port = query.get("origin_port", "").lower()
        destination_port = query.get("destination_port", "").lower()
        cargo_weight = query.get("cargo_weight", 0)
        
        available_vessels = []
        for vessel in self._maritime_data["vessels"]:
            if vessel["status"] == "available":
                # Verificar capacidad
                if vessel["capacity_tonnes"] >= cargo_weight:
                    # Verificar ruta
                    vessel_route = vessel["route"].lower()
                    if origin_port in vessel_route and destination_port in vessel_route:
                        available_vessels.append({
                            "vessel_id": vessel["vessel_id"],
                            "name": vessel["name"],
                            "capacity_tonnes": vessel["capacity_tonnes"],
                            "current_location": vessel["current_location"],
                            "next_departure": vessel["next_departure"],
                            "cost_per_ton": vessel["cost_per_ton"],
                            "transit_time_days": vessel["transit_time_days"],
                            "utilization_rate": min(100, (cargo_weight / vessel["capacity_tonnes"]) * 100)
                        })
        
        return {
            "query_type": "get_available_vessels",
            "result": {
                "available_vessels": available_vessels,
                "total_available": len(available_vessels),
                "origin_port": origin_port,
                "destination_port": destination_port,
                "cargo_weight": cargo_weight
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_port_schedules(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene horarios y disponibilidad de puertos."""
        port_name = query.get("origin_port", "").lower()
        
        if port_name not in self._maritime_data["ports"]:
            raise ToolError(f"Puerto no encontrado: {port_name}")
        
        port_info = self._maritime_data["ports"][port_name]
        
        # Simular horarios de carga
        loading_schedule = []
        current_time = datetime.now()
        for i in range(7):  # Próximos 7 días
            schedule_date = current_time + timedelta(days=i)
            loading_schedule.append({
                "date": schedule_date.strftime("%Y-%m-%d"),
                "available_slots": random.randint(2, 6),
                "loading_rate_tonnes_per_day": port_info["loading_rate_tonnes_per_day"],
                "estimated_wait_time_hours": random.randint(0, 12)
            })
        
        return {
            "query_type": "get_port_schedules",
            "result": {
                "port_name": port_info["name"],
                "country": port_info["country"],
                "capacity": port_info["capacity"],
                "loading_schedule": loading_schedule,
                "facilities": port_info["facilities"],
                "lay_time_hours": port_info["lay_time_hours"]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_freight(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula el costo de flete marítimo."""
        origin_port = query.get("origin_port", "").lower()
        destination_port = query.get("destination_port", "").lower()
        cargo_weight = query.get("cargo_weight", 0)
        
        # Buscar ruta
        route_key = f"{origin_port}_{destination_port}"
        if route_key not in self._maritime_data["routes"]:
            raise ToolError(f"Ruta no encontrada: {origin_port} -> {destination_port}")
        
        route = self._maritime_data["routes"][route_key]
        
        # Calcular costos
        base_freight_rate = 4.5  # USD por tonelada
        fuel_surcharge = route["fuel_cost_per_ton"]
        weather_surcharge = route["weather_factor"] - 1.0
        port_charges = 0.3  # USD por tonelada
        
        total_freight_per_ton = base_freight_rate + fuel_surcharge + (weather_surcharge * base_freight_rate) + port_charges
        total_freight_cost = total_freight_per_ton * cargo_weight
        
        return {
            "query_type": "calculate_freight",
            "result": {
                "origin_port": route["origin"],
                "destination_port": route["destination"],
                "cargo_weight": cargo_weight,
                "distance_nm": route["distance_nm"],
                "transit_time_days": route["transit_time_days"],
                "freight_breakdown": {
                    "base_freight_rate": base_freight_rate,
                    "fuel_surcharge": fuel_surcharge,
                    "weather_surcharge": weather_surcharge * base_freight_rate,
                    "port_charges": port_charges,
                    "total_per_ton": total_freight_per_ton
                },
                "total_freight_cost": round(total_freight_cost, 2),
                "currency": "USD"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_lay_time(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza tiempos de estadía en puertos."""
        port_name = query.get("origin_port", "").lower()
        cargo_weight = query.get("cargo_weight", 0)
        
        if port_name not in self._maritime_data["ports"]:
            raise ToolError(f"Puerto no encontrado: {port_name}")
        
        port_info = self._maritime_data["ports"][port_name]
        
        # Calcular tiempos de estadía
        loading_time_hours = (cargo_weight / port_info["loading_rate_tonnes_per_day"]) * 24
        administrative_time_hours = 6  # Tiempo administrativo
        total_lay_time_hours = loading_time_hours + administrative_time_hours + port_info["lay_time_hours"]
        
        # Simular demoras potenciales
        weather_delay_hours = random.randint(0, 12)
        congestion_delay_hours = random.randint(0, 8)
        
        return {
            "query_type": "analyze_lay_time",
            "result": {
                "port_name": port_info["name"],
                "cargo_weight": cargo_weight,
                "lay_time_breakdown": {
                    "loading_time_hours": round(loading_time_hours, 2),
                    "administrative_time_hours": administrative_time_hours,
                    "port_lay_time_hours": port_info["lay_time_hours"],
                    "weather_delay_hours": weather_delay_hours,
                    "congestion_delay_hours": congestion_delay_hours
                },
                "total_lay_time_hours": round(total_lay_time_hours + weather_delay_hours + congestion_delay_hours, 2),
                "estimated_departure": (datetime.now() + timedelta(hours=total_lay_time_hours + weather_delay_hours + congestion_delay_hours)).isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_maritime_routes(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene rutas marítimas disponibles."""
        origin_port = query.get("origin_port", "").lower()
        destination_port = query.get("destination_port", "").lower()
        
        available_routes = []
        for route_key, route in self._maritime_data["routes"].items():
            if origin_port in route["origin"].lower() and destination_port in route["destination"].lower():
                available_routes.append({
                    "route_id": route_key,
                    "origin": route["origin"],
                    "destination": route["destination"],
                    "distance_nm": route["distance_nm"],
                    "transit_time_days": route["transit_time_days"],
                    "weather_factor": route["weather_factor"],
                    "fuel_cost_per_ton": route["fuel_cost_per_ton"]
                })
        
        return {
            "query_type": "get_maritime_routes",
            "result": {
                "available_routes": available_routes,
                "total_routes": len(available_routes),
                "origin_port": origin_port,
                "destination_port": destination_port
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_vessel_capacity(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica capacidad de buques específicos."""
        vessel_id = query.get("vessel_id", "")
        cargo_weight = query.get("cargo_weight", 0)
        
        vessel = None
        for v in self._maritime_data["vessels"]:
            if v["vessel_id"] == vessel_id:
                vessel = v
                break
        
        if not vessel:
            raise ToolError(f"Buque no encontrado: {vessel_id}")
        
        capacity_available = vessel["capacity_tonnes"] - cargo_weight
        utilization_rate = (cargo_weight / vessel["capacity_tonnes"]) * 100
        
        return {
            "query_type": "check_vessel_capacity",
            "result": {
                "vessel_id": vessel["vessel_id"],
                "vessel_name": vessel["name"],
                "total_capacity_tonnes": vessel["capacity_tonnes"],
                "requested_cargo_weight": cargo_weight,
                "capacity_available": capacity_available,
                "utilization_rate": round(utilization_rate, 2),
                "can_accommodate": capacity_available >= 0,
                "current_location": vessel["current_location"],
                "status": vessel["status"]
            },
            "timestamp": datetime.now().isoformat()
        }


def create_maritime_partner_tool() -> FunctionTool:
    """
    Crea una instancia de FunctionTool para MaritimePartnerTool.
    
    Returns:
        FunctionTool configurada para uso con Google ADK
    """
    tool_instance = MaritimePartnerTool()
    
    return FunctionTool(
        name=tool_instance.name,
        description=tool_instance.description,
        func=tool_instance.execute
    )
