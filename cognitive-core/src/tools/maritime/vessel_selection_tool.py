"""
Vessel Selection Tool para el MaritimeLogisticsAgent.

Esta herramienta simula la selección inteligente de buques basada en criterios
de capacidad, costo, disponibilidad y eficiencia operativa.
"""

import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base_tool import BaseTool, FunctionTool
from ...shared.types import ToolConfig, ToolType
from ...shared.exceptions import ToolError
from ...shared.utils import get_logger


class VesselSelectionTool(BaseTool):
    """
    Herramienta para selección inteligente de buques.
    
    Implementa algoritmos de optimización para seleccionar el buque más adecuado
    basado en múltiples criterios como capacidad, costo, tiempo de tránsito,
    disponibilidad y eficiencia operativa.
    """
    
    def __init__(self):
        super().__init__(
            name="vessel_selection_tool",
            description="Herramienta para selección inteligente de buques",
            tool_type=ToolType.FUNCTION_TOOL,
            config=ToolConfig(
                name="vessel_selection_tool",
                type=ToolType.FUNCTION_TOOL,
                description="Herramienta para selección inteligente de buques",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query_type": {
                            "type": "string",
                            "enum": [
                                "select_optimal_vessel",
                                "compare_vessels",
                                "get_vessel_recommendations",
                                "analyze_vessel_efficiency",
                                "check_vessel_availability",
                                "calculate_vessel_costs"
                            ],
                            "description": "Tipo de consulta a realizar"
                        },
                        "cargo_weight": {
                            "type": "number",
                            "description": "Peso de la carga en toneladas"
                        },
                        "origin_port": {
                            "type": "string",
                            "description": "Puerto de origen"
                        },
                        "destination_port": {
                            "type": "string",
                            "description": "Puerto de destino"
                        },
                        "departure_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Fecha de salida deseada"
                        },
                        "priority_criteria": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["cost", "speed", "capacity", "reliability"]
                            },
                            "description": "Criterios de prioridad para selección"
                        },
                        "max_cost_per_ton": {
                            "type": "number",
                            "description": "Costo máximo por tonelada"
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
        
        # Base de datos simulada de buques
        self._vessel_database = {
            "vessels": [
                {
                    "vessel_id": "MV_ARGOS_CARRIER",
                    "name": "MV Argos Carrier",
                    "type": "bulk_carrier",
                    "capacity_tonnes": 8000,
                    "current_location": "Puerto Cartagena",
                    "next_departure": "2024-11-20",
                    "route": "Cartagena - Mobile, Alabama",
                    "cost_per_ton": 4.5,
                    "transit_time_days": 8,
                    "fuel_efficiency": 0.85,
                    "reliability_score": 0.92,
                    "age_years": 5,
                    "status": "available",
                    "specializations": ["cement", "bulk_cargo"],
                    "port_restrictions": [],
                    "weather_tolerance": "high"
                },
                {
                    "vessel_id": "MV_CEMENT_EXPRESS",
                    "name": "MV Cement Express",
                    "type": "cement_carrier",
                    "capacity_tonnes": 12000,
                    "current_location": "Puerto Barranquilla",
                    "next_departure": "2024-11-25",
                    "route": "Barranquilla - Mobile, Alabama",
                    "cost_per_ton": 4.2,
                    "transit_time_days": 9,
                    "fuel_efficiency": 0.88,
                    "reliability_score": 0.89,
                    "age_years": 3,
                    "status": "available",
                    "specializations": ["cement"],
                    "port_restrictions": [],
                    "weather_tolerance": "medium"
                },
                {
                    "vessel_id": "MV_LOGISTICS_PRO",
                    "name": "MV Logistics Pro",
                    "type": "multi_purpose",
                    "capacity_tonnes": 15000,
                    "current_location": "Puerto Buenaventura",
                    "next_departure": "2024-12-01",
                    "route": "Buenaventura - Mobile, Alabama",
                    "cost_per_ton": 4.8,
                    "transit_time_days": 12,
                    "fuel_efficiency": 0.82,
                    "reliability_score": 0.95,
                    "age_years": 2,
                    "status": "maintenance",
                    "specializations": ["cement", "bulk_cargo", "containers"],
                    "port_restrictions": ["requires_deep_water"],
                    "weather_tolerance": "high"
                },
                {
                    "vessel_id": "MV_COASTAL_RUNNER",
                    "name": "MV Coastal Runner",
                    "type": "coastal_carrier",
                    "capacity_tonnes": 5000,
                    "current_location": "Puerto Cartagena",
                    "next_departure": "2024-11-18",
                    "route": "Cartagena - Mobile, Alabama",
                    "cost_per_ton": 5.2,
                    "transit_time_days": 10,
                    "fuel_efficiency": 0.75,
                    "reliability_score": 0.85,
                    "age_years": 8,
                    "status": "available",
                    "specializations": ["cement", "bulk_cargo"],
                    "port_restrictions": ["shallow_draft_only"],
                    "weather_tolerance": "low"
                }
            ],
            "routes": {
                "cartagena_mobile": {
                    "distance_nm": 1200,
                    "weather_risk": "low",
                    "port_facilities": "excellent",
                    "congestion_factor": 1.1
                },
                "barranquilla_mobile": {
                    "distance_nm": 1350,
                    "weather_risk": "medium",
                    "port_facilities": "good",
                    "congestion_factor": 1.2
                },
                "buenaventura_mobile": {
                    "distance_nm": 1800,
                    "weather_risk": "high",
                    "port_facilities": "good",
                    "congestion_factor": 1.3
                }
            }
        }
    
    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una consulta específica de selección de buques.
        
        Args:
            query: Diccionario con los parámetros de la consulta
            
        Returns:
            Diccionario con el resultado de la consulta
        """
        query_type = query.get("query_type")
        self.logger.info(f"Ejecutando consulta de selección de buques: {query_type}")
        
        try:
            if query_type == "select_optimal_vessel":
                return self._select_optimal_vessel(query)
            elif query_type == "compare_vessels":
                return self._compare_vessels(query)
            elif query_type == "get_vessel_recommendations":
                return self._get_vessel_recommendations(query)
            elif query_type == "analyze_vessel_efficiency":
                return self._analyze_vessel_efficiency(query)
            elif query_type == "check_vessel_availability":
                return self._check_vessel_availability(query)
            elif query_type == "calculate_vessel_costs":
                return self._calculate_vessel_costs(query)
            else:
                raise ToolError(f"Tipo de consulta no soportado: {query_type}")
                
        except Exception as e:
            self.logger.error(f"Error ejecutando consulta de selección de buques: {e}")
            raise ToolError(f"Error en selección de buques: {e}")
    
    def _select_optimal_vessel(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Selecciona el buque óptimo basado en criterios múltiples."""
        cargo_weight = query.get("cargo_weight", 0)
        origin_port = query.get("origin_port", "").lower()
        destination_port = query.get("destination_port", "").lower()
        priority_criteria = query.get("priority_criteria", ["cost", "speed"])
        max_cost_per_ton = query.get("max_cost_per_ton", 10.0)
        
        # Filtrar buques disponibles y compatibles
        eligible_vessels = []
        for vessel in self._vessel_database["vessels"]:
            if vessel["status"] != "available":
                continue
            
            # Verificar capacidad
            if vessel["capacity_tonnes"] < cargo_weight:
                continue
            
            # Verificar costo máximo
            if vessel["cost_per_ton"] > max_cost_per_ton:
                continue
            
            # Verificar ruta
            vessel_route = vessel["route"].lower()
            if origin_port not in vessel_route or destination_port not in vessel_route:
                continue
            
            # Calcular score de optimización
            optimization_score = self._calculate_optimization_score(
                vessel, cargo_weight, priority_criteria
            )
            
            eligible_vessels.append({
                **vessel,
                "optimization_score": optimization_score,
                "utilization_rate": (cargo_weight / vessel["capacity_tonnes"]) * 100
            })
        
        if not eligible_vessels:
            return {
                "query_type": "select_optimal_vessel",
                "result": {
                    "optimal_vessel": None,
                    "message": "No se encontraron buques disponibles que cumplan los criterios",
                    "eligible_vessels": []
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # Ordenar por score de optimización
        eligible_vessels.sort(key=lambda x: x["optimization_score"], reverse=True)
        optimal_vessel = eligible_vessels[0]
        
        return {
            "query_type": "select_optimal_vessel",
            "result": {
                "optimal_vessel": {
                    "vessel_id": optimal_vessel["vessel_id"],
                    "name": optimal_vessel["name"],
                    "type": optimal_vessel["type"],
                    "capacity_tonnes": optimal_vessel["capacity_tonnes"],
                    "cost_per_ton": optimal_vessel["cost_per_ton"],
                    "transit_time_days": optimal_vessel["transit_time_days"],
                    "optimization_score": optimal_vessel["optimization_score"],
                    "utilization_rate": optimal_vessel["utilization_rate"],
                    "next_departure": optimal_vessel["next_departure"],
                    "reliability_score": optimal_vessel["reliability_score"]
                },
                "alternatives": eligible_vessels[1:3],  # Top 3 alternativas
                "selection_criteria": priority_criteria,
                "total_eligible": len(eligible_vessels)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _compare_vessels(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Compara múltiples buques para una carga específica."""
        cargo_weight = query.get("cargo_weight", 0)
        vessel_ids = query.get("vessel_ids", [])
        
        if not vessel_ids:
            # Si no se especifican IDs, usar todos los disponibles
            vessel_ids = [v["vessel_id"] for v in self._vessel_database["vessels"] if v["status"] == "available"]
        
        comparison_data = []
        for vessel_id in vessel_ids:
            vessel = next((v for v in self._vessel_database["vessels"] if v["vessel_id"] == vessel_id), None)
            if not vessel:
                continue
            
            # Calcular métricas de comparación
            total_cost = vessel["cost_per_ton"] * cargo_weight
            utilization_rate = (cargo_weight / vessel["capacity_tonnes"]) * 100
            efficiency_score = vessel["fuel_efficiency"] * vessel["reliability_score"]
            
            comparison_data.append({
                "vessel_id": vessel["vessel_id"],
                "name": vessel["name"],
                "type": vessel["type"],
                "capacity_tonnes": vessel["capacity_tonnes"],
                "cost_per_ton": vessel["cost_per_ton"],
                "total_cost": total_cost,
                "transit_time_days": vessel["transit_time_days"],
                "utilization_rate": utilization_rate,
                "efficiency_score": efficiency_score,
                "reliability_score": vessel["reliability_score"],
                "fuel_efficiency": vessel["fuel_efficiency"],
                "age_years": vessel["age_years"],
                "can_accommodate": vessel["capacity_tonnes"] >= cargo_weight
            })
        
        # Ordenar por costo total
        comparison_data.sort(key=lambda x: x["total_cost"])
        
        return {
            "query_type": "compare_vessels",
            "result": {
                "vessel_comparison": comparison_data,
                "cargo_weight": cargo_weight,
                "total_vessels_compared": len(comparison_data),
                "best_cost_option": comparison_data[0] if comparison_data else None,
                "best_time_option": min(comparison_data, key=lambda x: x["transit_time_days"]) if comparison_data else None
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_vessel_recommendations(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene recomendaciones de buques basadas en criterios específicos."""
        cargo_weight = query.get("cargo_weight", 0)
        origin_port = query.get("origin_port", "").lower()
        destination_port = query.get("destination_port", "").lower()
        
        recommendations = {
            "cost_optimized": [],
            "time_optimized": [],
            "capacity_optimized": [],
            "reliability_optimized": []
        }
        
        for vessel in self._vessel_database["vessels"]:
            if vessel["status"] != "available":
                continue
            
            if vessel["capacity_tonnes"] < cargo_weight:
                continue
            
            vessel_route = vessel["route"].lower()
            if origin_port not in vessel_route or destination_port not in vessel_route:
                continue
            
            vessel_data = {
                "vessel_id": vessel["vessel_id"],
                "name": vessel["name"],
                "cost_per_ton": vessel["cost_per_ton"],
                "transit_time_days": vessel["transit_time_days"],
                "capacity_tonnes": vessel["capacity_tonnes"],
                "reliability_score": vessel["reliability_score"],
                "utilization_rate": (cargo_weight / vessel["capacity_tonnes"]) * 100
            }
            
            # Clasificar por criterios
            recommendations["cost_optimized"].append(vessel_data)
            recommendations["time_optimized"].append(vessel_data)
            recommendations["capacity_optimized"].append(vessel_data)
            recommendations["reliability_optimized"].append(vessel_data)
        
        # Ordenar cada categoría
        recommendations["cost_optimized"].sort(key=lambda x: x["cost_per_ton"])
        recommendations["time_optimized"].sort(key=lambda x: x["transit_time_days"])
        recommendations["capacity_optimized"].sort(key=lambda x: x["utilization_rate"], reverse=True)
        recommendations["reliability_optimized"].sort(key=lambda x: x["reliability_score"], reverse=True)
        
        return {
            "query_type": "get_vessel_recommendations",
            "result": {
                "recommendations": recommendations,
                "cargo_weight": cargo_weight,
                "route": f"{origin_port} -> {destination_port}"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_vessel_efficiency(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la eficiencia operativa de buques."""
        vessel_id = query.get("vessel_id", "")
        
        vessel = next((v for v in self._vessel_database["vessels"] if v["vessel_id"] == vessel_id), None)
        if not vessel:
            raise ToolError(f"Buque no encontrado: {vessel_id}")
        
        # Calcular métricas de eficiencia
        fuel_efficiency_score = vessel["fuel_efficiency"]
        reliability_score = vessel["reliability_score"]
        age_factor = max(0.5, 1.0 - (vessel["age_years"] / 20))  # Factor de edad
        utilization_potential = min(1.0, vessel["capacity_tonnes"] / 10000)  # Potencial de utilización
        
        overall_efficiency = (fuel_efficiency_score * 0.3 + 
                             reliability_score * 0.4 + 
                             age_factor * 0.2 + 
                             utilization_potential * 0.1)
        
        return {
            "query_type": "analyze_vessel_efficiency",
            "result": {
                "vessel_id": vessel["vessel_id"],
                "vessel_name": vessel["name"],
                "efficiency_metrics": {
                    "fuel_efficiency": fuel_efficiency_score,
                    "reliability_score": reliability_score,
                    "age_factor": age_factor,
                    "utilization_potential": utilization_potential,
                    "overall_efficiency": round(overall_efficiency, 3)
                },
                "recommendations": self._get_efficiency_recommendations(vessel, overall_efficiency)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_vessel_availability(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica disponibilidad de buques en un período específico."""
        departure_date = query.get("departure_date")
        origin_port = query.get("origin_port", "").lower()
        
        available_vessels = []
        for vessel in self._vessel_database["vessels"]:
            if vessel["status"] == "available":
                vessel_route = vessel["route"].lower()
                if origin_port in vessel_route:
                    # Simular disponibilidad basada en fecha
                    vessel_departure = datetime.strptime(vessel["next_departure"], "%Y-%m-%d")
                    if departure_date:
                        requested_date = datetime.strptime(departure_date, "%Y-%m-%d")
                        days_diff = (requested_date - vessel_departure).days
                        availability_score = max(0, 1.0 - abs(days_diff) / 30)  # Score basado en proximidad
                    else:
                        availability_score = 1.0
                    
                    available_vessels.append({
                        "vessel_id": vessel["vessel_id"],
                        "name": vessel["name"],
                        "next_departure": vessel["next_departure"],
                        "availability_score": availability_score,
                        "current_location": vessel["current_location"]
                    })
        
        available_vessels.sort(key=lambda x: x["availability_score"], reverse=True)
        
        return {
            "query_type": "check_vessel_availability",
            "result": {
                "available_vessels": available_vessels,
                "departure_date": departure_date,
                "origin_port": origin_port,
                "total_available": len(available_vessels)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_vessel_costs(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula costos detallados para un buque específico."""
        vessel_id = query.get("vessel_id", "")
        cargo_weight = query.get("cargo_weight", 0)
        
        vessel = next((v for v in self._vessel_database["vessels"] if v["vessel_id"] == vessel_id), None)
        if not vessel:
            raise ToolError(f"Buque no encontrado: {vessel_id}")
        
        # Calcular costos detallados
        base_freight = vessel["cost_per_ton"] * cargo_weight
        fuel_cost = base_freight * 0.3  # 30% del costo base
        port_charges = cargo_weight * 0.5  # USD 0.5 por tonelada
        insurance_cost = base_freight * 0.05  # 5% del costo base
        handling_cost = cargo_weight * 0.3  # USD 0.3 por tonelada
        
        total_cost = base_freight + fuel_cost + port_charges + insurance_cost + handling_cost
        
        return {
            "query_type": "calculate_vessel_costs",
            "result": {
                "vessel_id": vessel["vessel_id"],
                "vessel_name": vessel["name"],
                "cargo_weight": cargo_weight,
                "cost_breakdown": {
                    "base_freight": round(base_freight, 2),
                    "fuel_cost": round(fuel_cost, 2),
                    "port_charges": round(port_charges, 2),
                    "insurance_cost": round(insurance_cost, 2),
                    "handling_cost": round(handling_cost, 2),
                    "total_cost": round(total_cost, 2)
                },
                "cost_per_ton": round(total_cost / cargo_weight, 2),
                "currency": "USD"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_optimization_score(self, vessel: Dict[str, Any], cargo_weight: int, priority_criteria: List[str]) -> float:
        """Calcula el score de optimización para un buque."""
        score = 0.0
        
        # Normalizar métricas
        cost_score = 1.0 - (vessel["cost_per_ton"] / 10.0)  # Normalizar costo (0-10 USD/ton)
        speed_score = 1.0 - (vessel["transit_time_days"] / 20.0)  # Normalizar tiempo (0-20 días)
        capacity_score = min(1.0, cargo_weight / vessel["capacity_tonnes"])  # Utilización
        reliability_score = vessel["reliability_score"]
        
        # Aplicar pesos basados en criterios de prioridad
        weights = {"cost": 0.0, "speed": 0.0, "capacity": 0.0, "reliability": 0.0}
        
        # Distribuir pesos basado en prioridades
        if "cost" in priority_criteria:
            weights["cost"] = 0.4
        if "speed" in priority_criteria:
            weights["speed"] = 0.3
        if "capacity" in priority_criteria:
            weights["capacity"] = 0.2
        if "reliability" in priority_criteria:
            weights["reliability"] = 0.1
        
        # Si no hay criterios específicos, usar distribución equilibrada
        if not priority_criteria:
            weights = {"cost": 0.3, "speed": 0.3, "capacity": 0.2, "reliability": 0.2}
        
        score = (cost_score * weights["cost"] + 
                speed_score * weights["speed"] + 
                capacity_score * weights["capacity"] + 
                reliability_score * weights["reliability"])
        
        return round(score, 3)
    
    def _get_efficiency_recommendations(self, vessel: Dict[str, Any], efficiency_score: float) -> List[str]:
        """Genera recomendaciones para mejorar la eficiencia del buque."""
        recommendations = []
        
        if vessel["fuel_efficiency"] < 0.8:
            recommendations.append("Considerar mejoras en eficiencia de combustible")
        
        if vessel["age_years"] > 10:
            recommendations.append("Evaluar renovación o modernización del buque")
        
        if vessel["reliability_score"] < 0.9:
            recommendations.append("Implementar programa de mantenimiento preventivo")
        
        if efficiency_score < 0.7:
            recommendations.append("Revisar estrategia operativa general")
        
        return recommendations


def create_vessel_selection_tool() -> FunctionTool:
    """
    Crea una instancia de FunctionTool para VesselSelectionTool.
    
    Returns:
        FunctionTool configurada para uso con Google ADK
    """
    tool_instance = VesselSelectionTool()
    
    return FunctionTool(
        name=tool_instance.name,
        description=tool_instance.description,
        func=tool_instance.execute
    )
