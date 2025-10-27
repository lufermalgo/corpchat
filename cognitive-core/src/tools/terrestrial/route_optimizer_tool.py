"""
Route Optimizer Tool para el TerrestrialLogisticsAgent.

Esta herramienta simula la optimización de rutas terrestres para Argos,
incluyendo cálculo de distancias, tiempos y costos de transporte.
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


class RouteOptimizerTool(BaseTool):
    """
    Herramienta para optimización de rutas terrestres.
    
    Simula el cálculo de rutas óptimas entre plantas de Argos y puertos,
    incluyendo análisis de costos, tiempos y eficiencia.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa la herramienta Route Optimizer.
        
        Args:
            config: Configuración de la herramienta
        """
        tool_config = ToolConfig(
            name="route_optimizer_tool",
            type=ToolType.FUNCTION_TOOL,
            description="Optimización de rutas terrestres con análisis de costos y tiempos",
            parameters=config or {}
        )
        super().__init__(tool_config)
        
        self._logger = get_logger(__name__)
        self._route_data = self._initialize_route_data()
        self._logger.info("Route Optimizer Tool inicializada")
    
    def _initialize_route_data(self) -> Dict[str, Any]:
        """
        Inicializa datos de rutas y costos.
        
        Returns:
            Diccionario con datos de rutas
        """
        # Ubicaciones principales de Argos
        locations = {
            "bogota": {
                "name": "Planta Bogotá",
                "coordinates": {"lat": 4.6097, "lon": -74.0817},
                "type": "plant"
            },
            "medellin": {
                "name": "Planta Medellín", 
                "coordinates": {"lat": 6.2442, "lon": -75.5812},
                "type": "plant"
            },
            "cali": {
                "name": "Planta Cali",
                "coordinates": {"lat": 3.4516, "lon": -76.5320},
                "type": "plant"
            },
            "cartagena": {
                "name": "Puerto Cartagena",
                "coordinates": {"lat": 10.3910, "lon": -75.4794},
                "type": "port"
            }
        }
        
        # Matriz de distancias (km) - datos realistas aproximados
        distances = {
            ("bogota", "cartagena"): 650,
            ("medellin", "cartagena"): 420,
            ("cali", "cartagena"): 580,
            ("bogota", "medellin"): 250,
            ("bogota", "cali"): 300,
            ("medellin", "cali"): 200
        }
        
        # Costos por kilómetro (USD) - incluye combustible, peajes, mantenimiento
        cost_per_km = {
            "standard": 0.15,  # Ruta estándar
            "highway": 0.12,   # Autopista (más eficiente)
            "mountain": 0.20   # Ruta montañosa (más costosa)
        }
        
        # Tipos de ruta disponibles
        route_types = {
            ("bogota", "cartagena"): ["highway", "standard"],
            ("medellin", "cartagena"): ["highway", "standard"],
            ("cali", "cartagena"): ["highway", "mountain", "standard"],
            ("bogota", "medellin"): ["highway", "standard"],
            ("bogota", "cali"): ["highway", "standard"],
            ("medellin", "cali"): ["highway", "mountain"]
        }
        
        return {
            "locations": locations,
            "distances": distances,
            "cost_per_km": cost_per_km,
            "route_types": route_types
        }
    
    def execute(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta optimización de ruta.
        
        Args:
            input_data: Datos de entrada con parámetros de optimización
            context: Contexto adicional (opcional)
            
        Returns:
            Resultado de la optimización de ruta
            
        Raises:
            ToolError: Si hay error ejecutando la optimización
        """
        try:
            query_type = input_data.get("query_type", "optimize_route")
            
            if query_type == "optimize_route":
                return self._optimize_route(input_data)
            elif query_type == "calculate_distance":
                return self._calculate_distance(input_data)
            elif query_type == "estimate_cost":
                return self._estimate_cost(input_data)
            elif query_type == "estimate_time":
                return self._estimate_time(input_data)
            elif query_type == "compare_routes":
                return self._compare_routes(input_data)
            else:
                raise ToolError(f"Tipo de consulta no soportado: {query_type}")
                
        except Exception as e:
            raise ToolError(f"Error ejecutando optimización de ruta: {e}")
    
    def _optimize_route(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimiza ruta entre origen y destino.
        
        Args:
            input_data: Parámetros de optimización
            
        Returns:
            Ruta optimizada
        """
        origin = input_data.get("origin", "").lower()
        destination = input_data.get("destination", "").lower()
        cargo_weight = input_data.get("cargo_weight", 0)
        priority = input_data.get("priority", "cost")  # cost, time, efficiency
        
        if not origin or not destination:
            raise ToolError("origin y destination son requeridos")
        
        # Validar ubicaciones
        if origin not in self._route_data["locations"]:
            raise ToolError(f"Ubicación origen no válida: {origin}")
        
        if destination not in self._route_data["locations"]:
            raise ToolError(f"Ubicación destino no válida: {destination}")
        
        # Obtener rutas disponibles
        route_key = tuple(sorted([origin, destination]))
        if route_key not in self._route_data["distances"]:
            raise ToolError(f"No hay ruta disponible entre {origin} y {destination}")
        
        distance = self._route_data["distances"][route_key]
        available_routes = self._route_data["route_types"].get(route_key, ["standard"])
        
        # Calcular opciones de ruta
        route_options = []
        for route_type in available_routes:
            cost_per_km = self._route_data["cost_per_km"][route_type]
            
            # Calcular costos y tiempos
            base_cost = distance * cost_per_km
            
            # Factor de peso (costo adicional por tonelada)
            weight_factor = 1 + (cargo_weight * 0.01)  # 1% adicional por tonelada
            total_cost = base_cost * weight_factor
            
            # Tiempo estimado (horas) - velocidad promedio por tipo de ruta
            avg_speed = {"highway": 80, "standard": 60, "mountain": 45}[route_type]
            estimated_time = distance / avg_speed
            
            # Factor de eficiencia
            efficiency_score = self._calculate_efficiency_score(route_type, distance, cargo_weight)
            
            route_options.append({
                "route_type": route_type,
                "distance_km": distance,
                "estimated_time_hours": round(estimated_time, 1),
                "estimated_cost_usd": round(total_cost, 2),
                "efficiency_score": round(efficiency_score, 2),
                "avg_speed_kmh": avg_speed
            })
        
        # Seleccionar ruta óptima según prioridad
        if priority == "cost":
            optimal_route = min(route_options, key=lambda r: r["estimated_cost_usd"])
        elif priority == "time":
            optimal_route = min(route_options, key=lambda r: r["estimated_time_hours"])
        else:  # efficiency
            optimal_route = max(route_options, key=lambda r: r["efficiency_score"])
        
        return {
            "query_type": "route_optimization",
            "timestamp": datetime.now().isoformat(),
            "origin": self._route_data["locations"][origin]["name"],
            "destination": self._route_data["locations"][destination]["name"],
            "cargo_weight": cargo_weight,
            "priority": priority,
            "optimal_route": optimal_route,
            "all_options": route_options,
            "recommendation": self._generate_route_recommendation(optimal_route, cargo_weight)
        }
    
    def _calculate_distance(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula distancia entre dos puntos.
        
        Args:
            input_data: Parámetros de cálculo
            
        Returns:
            Distancia calculada
        """
        origin = input_data.get("origin", "").lower()
        destination = input_data.get("destination", "").lower()
        
        if not origin or not destination:
            raise ToolError("origin y destination son requeridos")
        
        route_key = tuple(sorted([origin, destination]))
        distance = self._route_data["distances"].get(route_key, 0)
        
        if distance == 0:
            raise ToolError(f"No hay ruta disponible entre {origin} y {destination}")
        
        return {
            "query_type": "distance_calculation",
            "timestamp": datetime.now().isoformat(),
            "origin": self._route_data["locations"][origin]["name"],
            "destination": self._route_data["locations"][destination]["name"],
            "distance_km": distance,
            "distance_miles": round(distance * 0.621371, 2)
        }
    
    def _estimate_cost(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estima costo de transporte.
        
        Args:
            input_data: Parámetros de estimación
            
        Returns:
            Estimación de costo
        """
        origin = input_data.get("origin", "").lower()
        destination = input_data.get("destination", "").lower()
        cargo_weight = input_data.get("cargo_weight", 0)
        route_type = input_data.get("route_type", "standard")
        
        route_key = tuple(sorted([origin, destination]))
        distance = self._route_data["distances"].get(route_key, 0)
        
        if distance == 0:
            raise ToolError(f"No hay ruta disponible entre {origin} y {destination}")
        
        cost_per_km = self._route_data["cost_per_km"].get(route_type, 0.15)
        base_cost = distance * cost_per_km
        
        # Factor de peso
        weight_factor = 1 + (cargo_weight * 0.01)
        total_cost = base_cost * weight_factor
        
        # Costos adicionales
        additional_costs = {
            "fuel": total_cost * 0.4,  # 40% del costo es combustible
            "tolls": total_cost * 0.15,  # 15% peajes
            "maintenance": total_cost * 0.1,  # 10% mantenimiento
            "driver": total_cost * 0.2,  # 20% conductor
            "other": total_cost * 0.15  # 15% otros
        }
        
        return {
            "query_type": "cost_estimation",
            "timestamp": datetime.now().isoformat(),
            "origin": self._route_data["locations"][origin]["name"],
            "destination": self._route_data["locations"][destination]["name"],
            "cargo_weight": cargo_weight,
            "route_type": route_type,
            "distance_km": distance,
            "total_cost_usd": round(total_cost, 2),
            "cost_breakdown": {k: round(v, 2) for k, v in additional_costs.items()},
            "cost_per_ton": round(total_cost / cargo_weight, 2) if cargo_weight > 0 else 0
        }
    
    def _estimate_time(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estima tiempo de transporte.
        
        Args:
            input_data: Parámetros de estimación
            
        Returns:
            Estimación de tiempo
        """
        origin = input_data.get("origin", "").lower()
        destination = input_data.get("destination", "").lower()
        route_type = input_data.get("route_type", "standard")
        
        route_key = tuple(sorted([origin, destination]))
        distance = self._route_data["distances"].get(route_key, 0)
        
        if distance == 0:
            raise ToolError(f"No hay ruta disponible entre {origin} y {destination}")
        
        # Velocidades promedio por tipo de ruta
        avg_speeds = {"highway": 80, "standard": 60, "mountain": 45}
        avg_speed = avg_speeds.get(route_type, 60)
        
        # Tiempo base de conducción
        driving_time = distance / avg_speed
        
        # Tiempos adicionales
        additional_times = {
            "loading_time": 2.0,  # 2 horas de carga
            "unloading_time": 1.5,  # 1.5 horas de descarga
            "rest_stops": max(0, (driving_time - 8) * 0.1),  # Paradas de descanso
            "traffic_delay": driving_time * 0.1,  # 10% retraso por tráfico
            "border_crossing": 0.5 if "cartagena" in [origin, destination] else 0
        }
        
        total_time = driving_time + sum(additional_times.values())
        
        # Fecha estimada de llegada
        departure_time = input_data.get("departure_time", datetime.now().isoformat())
        try:
            departure_dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
        except:
            departure_dt = datetime.now()
        
        arrival_dt = departure_dt + timedelta(hours=total_time)
        
        return {
            "query_type": "time_estimation",
            "timestamp": datetime.now().isoformat(),
            "origin": self._route_data["locations"][origin]["name"],
            "destination": self._route_data["locations"][destination]["name"],
            "route_type": route_type,
            "distance_km": distance,
            "driving_time_hours": round(driving_time, 1),
            "total_time_hours": round(total_time, 1),
            "departure_time": departure_time,
            "estimated_arrival": arrival_dt.isoformat(),
            "time_breakdown": {k: round(v, 1) for k, v in additional_times.items()}
        }
    
    def _compare_routes(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compara múltiples rutas.
        
        Args:
            input_data: Parámetros de comparación
            
        Returns:
            Comparación de rutas
        """
        origin = input_data.get("origin", "").lower()
        destination = input_data.get("destination", "").lower()
        cargo_weight = input_data.get("cargo_weight", 0)
        
        route_key = tuple(sorted([origin, destination]))
        available_routes = self._route_data["route_types"].get(route_key, ["standard"])
        
        comparison = []
        for route_type in available_routes:
            route_data = self._optimize_route({
                "origin": origin,
                "destination": destination,
                "cargo_weight": cargo_weight,
                "priority": "efficiency"
            })
            
            optimal_route = route_data["optimal_route"]
            comparison.append({
                "route_type": route_type,
                "distance_km": optimal_route["distance_km"],
                "estimated_time_hours": optimal_route["estimated_time_hours"],
                "estimated_cost_usd": optimal_route["estimated_cost_usd"],
                "efficiency_score": optimal_route["efficiency_score"]
            })
        
        # Encontrar mejores opciones
        best_cost = min(comparison, key=lambda r: r["estimated_cost_usd"])
        best_time = min(comparison, key=lambda r: r["estimated_time_hours"])
        best_efficiency = max(comparison, key=lambda r: r["efficiency_score"])
        
        return {
            "query_type": "route_comparison",
            "timestamp": datetime.now().isoformat(),
            "origin": self._route_data["locations"][origin]["name"],
            "destination": self._route_data["locations"][destination]["name"],
            "cargo_weight": cargo_weight,
            "routes": comparison,
            "best_options": {
                "lowest_cost": best_cost,
                "fastest": best_time,
                "most_efficient": best_efficiency
            }
        }
    
    def _calculate_efficiency_score(self, route_type: str, distance: float, cargo_weight: float) -> float:
        """
        Calcula score de eficiencia de ruta.
        
        Args:
            route_type: Tipo de ruta
            distance: Distancia en km
            cargo_weight: Peso de la carga
            
        Returns:
            Score de eficiencia (0-1)
        """
        # Factores de eficiencia
        route_efficiency = {"highway": 0.9, "standard": 0.7, "mountain": 0.5}[route_type]
        distance_efficiency = min(1.0, 1000 / distance)  # Rutas más cortas son más eficientes
        weight_efficiency = min(1.0, cargo_weight / 1000)  # Cargas más grandes son más eficientes
        
        # Score combinado
        efficiency_score = (route_efficiency * 0.4 + distance_efficiency * 0.3 + weight_efficiency * 0.3)
        
        return min(1.0, efficiency_score)
    
    def _generate_route_recommendation(self, route: Dict[str, Any], cargo_weight: float) -> str:
        """
        Genera recomendación basada en la ruta óptima.
        
        Args:
            route: Datos de la ruta óptima
            cargo_weight: Peso de la carga
            
        Returns:
            Recomendación textual
        """
        route_type = route["route_type"]
        time_hours = route["estimated_time_hours"]
        cost = route["estimated_cost_usd"]
        
        recommendations = {
            "highway": f"Ruta recomendada por autopista: {time_hours}h de viaje, ${cost} de costo. Ideal para carga de {cargo_weight} toneladas.",
            "standard": f"Ruta estándar recomendada: {time_hours}h de viaje, ${cost} de costo. Balance óptimo entre tiempo y costo.",
            "mountain": f"Ruta montañosa: {time_hours}h de viaje, ${cost} de costo. Considerar solo si es la única opción disponible."
        }
        
        return recommendations.get(route_type, "Ruta optimizada según parámetros especificados.")


def create_route_optimizer_tool() -> FunctionTool:
    """
    Crea una instancia de Route Optimizer Tool como FunctionTool.
    
    Returns:
        FunctionTool configurada para optimización de rutas
    """
    route_tool = RouteOptimizerTool()
    
    def route_optimizer_function(query_type: str = "optimize_route", **kwargs) -> Dict[str, Any]:
        """
        Función wrapper para Route Optimizer Tool.
        
        Args:
            query_type: Tipo de consulta de optimización
            **kwargs: Parámetros adicionales
            
        Returns:
            Resultado de la optimización de ruta
        """
        input_data = {"query_type": query_type, **kwargs}
        return route_tool.execute(input_data)
    
    # Configurar FunctionTool
    tool_config = ToolConfig(
        name="route_optimizer_tool",
        type=ToolType.FUNCTION_TOOL,
        description="Optimización de rutas terrestres con análisis de costos y tiempos"
    )
    
    return FunctionTool(route_optimizer_function, tool_config)
