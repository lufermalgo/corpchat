"""
Geofence Tool para el TerrestrialLogisticsAgent.

Esta herramienta simula el monitoreo de geocercas para la flota de Argos,
incluyendo alertas de entrada/salida y seguimiento de ubicaciones críticas.
"""

import logging
import random
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

from ..base_tool import BaseTool, FunctionTool
from ...shared.types import ToolConfig, ToolType
from ...shared.exceptions import ToolError
from ...shared.utils import get_logger


class GeofenceTool(BaseTool):
    """
    Herramienta para monitoreo de geocercas.
    
    Simula el sistema de geocercas de Argos para monitoreo de ubicaciones
    críticas como plantas, puertos y zonas de alto riesgo.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa la herramienta Geofence.
        
        Args:
            config: Configuración de la herramienta
        """
        tool_config = ToolConfig(
            name="geofence_tool",
            type=ToolType.FUNCTION_TOOL,
            description="Monitoreo de geocercas para seguimiento de ubicaciones críticas",
            parameters=config or {}
        )
        super().__init__(tool_config)
        
        self._logger = get_logger(__name__)
        self._geofence_data = self._initialize_geofence_data()
        self._logger.info("Geofence Tool inicializada")
    
    def _initialize_geofence_data(self) -> Dict[str, Any]:
        """
        Inicializa datos de geocercas.
        
        Returns:
            Diccionario con datos de geocercas
        """
        # Geocercas críticas de Argos
        geofences = {
            "bogota_plant": {
                "name": "Planta Bogotá",
                "type": "plant",
                "center": {"lat": 4.6097, "lon": -74.0817},
                "radius_km": 2.0,
                "priority": "high",
                "alerts_enabled": True,
                "max_capacity": 50,
                "current_vehicles": 12
            },
            "medellin_plant": {
                "name": "Planta Medellín",
                "type": "plant", 
                "center": {"lat": 6.2442, "lon": -75.5812},
                "radius_km": 2.0,
                "priority": "high",
                "alerts_enabled": True,
                "max_capacity": 30,
                "current_vehicles": 8
            },
            "cali_plant": {
                "name": "Planta Cali",
                "type": "plant",
                "center": {"lat": 3.4516, "lon": -76.5320},
                "radius_km": 2.0,
                "priority": "high",
                "alerts_enabled": True,
                "max_capacity": 40,
                "current_vehicles": 15
            },
            "cartagena_port": {
                "name": "Puerto Cartagena",
                "type": "port",
                "center": {"lat": 10.3910, "lon": -75.4794},
                "radius_km": 5.0,
                "priority": "critical",
                "alerts_enabled": True,
                "max_capacity": 100,
                "current_vehicles": 25
            },
            "highway_toll_1": {
                "name": "Peaje Autopista Norte",
                "type": "toll",
                "center": {"lat": 4.8, "lon": -74.0},
                "radius_km": 0.5,
                "priority": "medium",
                "alerts_enabled": True,
                "max_capacity": 20,
                "current_vehicles": 5
            },
            "highway_toll_2": {
                "name": "Peaje Autopista Sur",
                "type": "toll",
                "center": {"lat": 3.2, "lon": -76.3},
                "radius_km": 0.5,
                "priority": "medium",
                "alerts_enabled": True,
                "max_capacity": 20,
                "current_vehicles": 3
            },
            "restricted_zone_1": {
                "name": "Zona Restringida Centro",
                "type": "restricted",
                "center": {"lat": 4.6, "lon": -74.08},
                "radius_km": 1.0,
                "priority": "critical",
                "alerts_enabled": True,
                "max_capacity": 0,
                "current_vehicles": 0
            }
        }
        
        # Alertas activas simuladas
        active_alerts = [
            {
                "alert_id": "ALERT-001",
                "geofence_id": "cartagena_port",
                "vehicle_id": "ARGOS-045",
                "alert_type": "entry",
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "status": "active",
                "message": "Vehículo ARGOS-045 ingresó a Puerto Cartagena"
            },
            {
                "alert_id": "ALERT-002", 
                "geofence_id": "bogota_plant",
                "vehicle_id": "ARGOS-023",
                "alert_type": "exit",
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "status": "resolved",
                "message": "Vehículo ARGOS-023 salió de Planta Bogotá"
            }
        ]
        
        return {
            "geofences": geofences,
            "active_alerts": active_alerts
        }
    
    def execute(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta consulta de geocercas.
        
        Args:
            input_data: Datos de entrada con parámetros de consulta
            context: Contexto adicional (opcional)
            
        Returns:
            Resultado de la consulta de geocercas
            
        Raises:
            ToolError: Si hay error ejecutando la consulta
        """
        try:
            query_type = input_data.get("query_type", "get_geofence_status")
            
            if query_type == "get_geofence_status":
                return self._get_geofence_status(input_data)
            elif query_type == "check_vehicle_location":
                return self._check_vehicle_location(input_data)
            elif query_type == "get_active_alerts":
                return self._get_active_alerts(input_data)
            elif query_type == "create_geofence":
                return self._create_geofence(input_data)
            elif query_type == "simulate_vehicle_movement":
                return self._simulate_vehicle_movement(input_data)
            else:
                raise ToolError(f"Tipo de consulta no soportado: {query_type}")
                
        except Exception as e:
            raise ToolError(f"Error ejecutando consulta de geocercas: {e}")
    
    def _get_geofence_status(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene estado de todas las geocercas.
        
        Args:
            input_data: Parámetros de consulta
            
        Returns:
            Estado de geocercas
        """
        geofence_type = input_data.get("type")  # plant, port, toll, restricted
        priority_filter = input_data.get("priority")  # high, critical, medium
        
        geofences = self._geofence_data["geofences"]
        
        # Filtrar por tipo si se especifica
        if geofence_type:
            geofences = {k: v for k, v in geofences.items() if v["type"] == geofence_type}
        
        # Filtrar por prioridad si se especifica
        if priority_filter:
            geofences = {k: v for k, v in geofences.items() if v["priority"] == priority_filter}
        
        # Calcular estadísticas
        total_geofences = len(geofences)
        total_capacity = sum(g["max_capacity"] for g in geofences.values())
        total_current = sum(g["current_vehicles"] for g in geofences.values())
        utilization_rate = (total_current / total_capacity * 100) if total_capacity > 0 else 0
        
        # Contar por tipo
        type_counts = {}
        for geofence in geofences.values():
            geofence_type = geofence["type"]
            type_counts[geofence_type] = type_counts.get(geofence_type, 0) + 1
        
        return {
            "query_type": "geofence_status",
            "timestamp": datetime.now().isoformat(),
            "filters": {
                "type": geofence_type,
                "priority": priority_filter
            },
            "summary": {
                "total_geofences": total_geofences,
                "total_capacity": total_capacity,
                "current_vehicles": total_current,
                "utilization_rate": round(utilization_rate, 1),
                "type_distribution": type_counts
            },
            "geofences": list(geofences.values())
        }
    
    def _check_vehicle_location(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica ubicación de un vehículo específico.
        
        Args:
            input_data: Parámetros de consulta
            
        Returns:
            Estado de ubicación del vehículo
        """
        vehicle_id = input_data.get("vehicle_id")
        vehicle_location = input_data.get("vehicle_location")  # {"lat": x, "lon": y}
        
        if not vehicle_id:
            raise ToolError("vehicle_id es requerido")
        
        if not vehicle_location:
            # Simular ubicación aleatoria si no se proporciona
            vehicle_location = {
                "lat": random.uniform(3.0, 7.0),
                "lon": random.uniform(-77.0, -73.0)
            }
        
        # Verificar en qué geocercas está el vehículo
        inside_geofences = []
        nearby_geofences = []
        
        for geofence_id, geofence in self._geofence_data["geofences"].items():
            distance = self._calculate_distance(
                vehicle_location["lat"], vehicle_location["lon"],
                geofence["center"]["lat"], geofence["center"]["lon"]
            )
            
            if distance <= geofence["radius_km"]:
                inside_geofences.append({
                    "geofence_id": geofence_id,
                    "name": geofence["name"],
                    "type": geofence["type"],
                    "priority": geofence["priority"],
                    "distance_km": round(distance, 2)
                })
            elif distance <= geofence["radius_km"] * 2:  # Cerca de la geocerca
                nearby_geofences.append({
                    "geofence_id": geofence_id,
                    "name": geofence["name"],
                    "type": geofence["type"],
                    "distance_km": round(distance, 2)
                })
        
        # Generar alertas si es necesario
        alerts_generated = []
        for geofence_info in inside_geofences:
            if geofence_info["priority"] in ["high", "critical"]:
                alerts_generated.append({
                    "alert_type": "entry",
                    "geofence_id": geofence_info["geofence_id"],
                    "vehicle_id": vehicle_id,
                    "message": f"Vehículo {vehicle_id} ingresó a {geofence_info['name']}"
                })
        
        return {
            "query_type": "vehicle_location_check",
            "timestamp": datetime.now().isoformat(),
            "vehicle_id": vehicle_id,
            "vehicle_location": vehicle_location,
            "inside_geofences": inside_geofences,
            "nearby_geofences": nearby_geofences,
            "alerts_generated": alerts_generated,
            "status": "inside" if inside_geofences else "outside"
        }
    
    def _get_active_alerts(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene alertas activas de geocercas.
        
        Args:
            input_data: Parámetros de consulta
            
        Returns:
            Lista de alertas activas
        """
        alert_type = input_data.get("alert_type")  # entry, exit, violation
        geofence_id = input_data.get("geofence_id")
        status_filter = input_data.get("status", "active")  # active, resolved
        
        alerts = self._geofence_data["active_alerts"]
        
        # Filtrar por tipo de alerta
        if alert_type:
            alerts = [a for a in alerts if a["alert_type"] == alert_type]
        
        # Filtrar por geocerca
        if geofence_id:
            alerts = [a for a in alerts if a["geofence_id"] == geofence_id]
        
        # Filtrar por estado
        alerts = [a for a in alerts if a["status"] == status_filter]
        
        # Estadísticas de alertas
        alert_stats = {
            "total_alerts": len(alerts),
            "by_type": {},
            "by_priority": {},
            "by_geofence": {}
        }
        
        for alert in alerts:
            # Por tipo
            alert_stats["by_type"][alert["alert_type"]] = alert_stats["by_type"].get(alert["alert_type"], 0) + 1
            
            # Por geocerca
            alert_stats["by_geofence"][alert["geofence_id"]] = alert_stats["by_geofence"].get(alert["geofence_id"], 0) + 1
            
            # Por prioridad (obtener de geocerca)
            geofence = self._geofence_data["geofences"].get(alert["geofence_id"], {})
            priority = geofence.get("priority", "unknown")
            alert_stats["by_priority"][priority] = alert_stats["by_priority"].get(priority, 0) + 1
        
        return {
            "query_type": "active_alerts",
            "timestamp": datetime.now().isoformat(),
            "filters": {
                "alert_type": alert_type,
                "geofence_id": geofence_id,
                "status": status_filter
            },
            "statistics": alert_stats,
            "alerts": alerts
        }
    
    def _create_geofence(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una nueva geocerca.
        
        Args:
            input_data: Parámetros de la geocerca
            
        Returns:
            Información de la geocerca creada
        """
        name = input_data.get("name")
        geofence_type = input_data.get("type", "custom")
        center = input_data.get("center")  # {"lat": x, "lon": y}
        radius_km = input_data.get("radius_km", 1.0)
        priority = input_data.get("priority", "medium")
        
        if not name or not center:
            raise ToolError("name y center son requeridos para crear geocerca")
        
        # Generar ID único
        geofence_id = f"custom_{len(self._geofence_data['geofences']) + 1}"
        
        # Crear geocerca
        new_geofence = {
            "name": name,
            "type": geofence_type,
            "center": center,
            "radius_km": radius_km,
            "priority": priority,
            "alerts_enabled": True,
            "max_capacity": input_data.get("max_capacity", 10),
            "current_vehicles": 0
        }
        
        # Agregar a datos
        self._geofence_data["geofences"][geofence_id] = new_geofence
        
        return {
            "query_type": "geofence_creation",
            "timestamp": datetime.now().isoformat(),
            "geofence_id": geofence_id,
            "geofence": new_geofence,
            "message": f"Geocerca '{name}' creada exitosamente"
        }
    
    def _simulate_vehicle_movement(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simula movimiento de vehículo y genera alertas.
        
        Args:
            input_data: Parámetros de simulación
            
        Returns:
            Resultado de la simulación
        """
        vehicle_id = input_data.get("vehicle_id", "ARGOS-SIM")
        start_location = input_data.get("start_location")
        end_location = input_data.get("end_location")
        duration_hours = input_data.get("duration_hours", 2.0)
        
        if not start_location or not end_location:
            raise ToolError("start_location y end_location son requeridos")
        
        # Simular movimiento paso a paso
        steps = int(duration_hours * 4)  # Cada 15 minutos
        alerts_generated = []
        
        for step in range(steps + 1):
            # Interpolar ubicación
            progress = step / steps
            current_lat = start_location["lat"] + (end_location["lat"] - start_location["lat"]) * progress
            current_lon = start_location["lon"] + (end_location["lon"] - start_location["lon"]) * progress
            
            current_location = {"lat": current_lat, "lon": current_lon}
            
            # Verificar geocercas
            location_check = self._check_vehicle_location({
                "vehicle_id": vehicle_id,
                "vehicle_location": current_location
            })
            
            # Agregar alertas generadas
            for alert in location_check["alerts_generated"]:
                alert["timestamp"] = (datetime.now() + timedelta(minutes=step * 15)).isoformat()
                alerts_generated.append(alert)
        
        return {
            "query_type": "vehicle_movement_simulation",
            "timestamp": datetime.now().isoformat(),
            "vehicle_id": vehicle_id,
            "start_location": start_location,
            "end_location": end_location,
            "duration_hours": duration_hours,
            "total_alerts": len(alerts_generated),
            "alerts_generated": alerts_generated,
            "simulation_completed": True
        }
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula distancia entre dos puntos geográficos (km).
        
        Args:
            lat1, lon1: Coordenadas del primer punto
            lat2, lon2: Coordenadas del segundo punto
            
        Returns:
            Distancia en kilómetros
        """
        # Fórmula de Haversine
        R = 6371  # Radio de la Tierra en km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c


def create_geofence_tool() -> FunctionTool:
    """
    Crea una instancia de Geofence Tool como FunctionTool.
    
    Returns:
        FunctionTool configurada para monitoreo de geocercas
    """
    geofence_tool = GeofenceTool()
    
    def geofence_function(query_type: str = "get_geofence_status", **kwargs) -> Dict[str, Any]:
        """
        Función wrapper para Geofence Tool.
        
        Args:
            query_type: Tipo de consulta de geocercas
            **kwargs: Parámetros adicionales
            
        Returns:
            Resultado de la consulta de geocercas
        """
        input_data = {"query_type": query_type, **kwargs}
        return geofence_tool.execute(input_data)
    
    # Configurar FunctionTool
    tool_config = ToolConfig(
        name="geofence_tool",
        type=ToolType.FUNCTION_TOOL,
        description="Monitoreo de geocercas para seguimiento de ubicaciones críticas"
    )
    
    return FunctionTool(geofence_function, tool_config)
