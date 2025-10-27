"""
Reverse Planning Tool para el MultimodalIntegrationAgent.

Esta herramienta implementa planificación inversa desde la demanda final
para determinar los puntos de origen óptimos y las fechas de inicio de transporte.
"""

import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base_tool import BaseTool, FunctionTool
from ...shared.types import ToolConfig, ToolType
from ...shared.exceptions import ToolError
from ...shared.utils import get_logger


class ReversePlanningTool(BaseTool):
    """
    Herramienta para planificación inversa multimodal.
    
    Implementa algoritmos de planificación inversa que:
    - Calculan hacia atrás desde la demanda final
    - Determinan puntos de origen óptimos
    - Optimizan fechas de inicio de transporte
    - Consideran restricciones de capacidad y tiempo
    """
    
    def __init__(self):
        super().__init__(
            name="reverse_planning_tool",
            description="Herramienta para planificación inversa multimodal",
            tool_type=ToolType.FUNCTION_TOOL,
            config=ToolConfig(
                name="reverse_planning_tool",
                type=ToolType.FUNCTION_TOOL,
                description="Herramienta para planificación inversa multimodal",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query_type": {
                            "type": "string",
                            "enum": [
                                "plan_from_demand",
                                "optimize_origin_selection",
                                "calculate_backward_schedule",
                                "analyze_capacity_constraints",
                                "optimize_multimodal_flow",
                                "validate_feasibility"
                            ],
                            "description": "Tipo de consulta a realizar"
                        },
                        "final_destination": {
                            "type": "string",
                            "description": "Destino final de la carga"
                        },
                        "required_quantity": {
                            "type": "number",
                            "description": "Cantidad requerida en toneladas"
                        },
                        "delivery_deadline": {
                            "type": "string",
                            "format": "date",
                            "description": "Fecha límite de entrega"
                        },
                        "cargo_type": {
                            "type": "string",
                            "description": "Tipo de carga (e.g., cemento)"
                        },
                        "available_origins": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Puntos de origen disponibles"
                        },
                        "transport_modes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Modos de transporte disponibles"
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
        
        # Base de datos simulada para planificación inversa
        self._planning_data = {
            "plants": {
                "bogota": {
                    "name": "Planta Bogotá",
                    "location": "Bogotá, Colombia",
                    "capacity_tonnes_per_day": 1000,
                    "available_capacity": 3000,
                    "distance_to_cartagena_km": 650,
                    "terrestrial_transit_time_hours": 8.1,
                    "terrestrial_cost_per_ton": 0.0975,
                    "specializations": ["cement", "concrete"]
                },
                "medellin": {
                    "name": "Planta Medellín",
                    "location": "Medellín, Colombia",
                    "capacity_tonnes_per_day": 800,
                    "available_capacity": 2000,
                    "distance_to_cartagena_km": 450,
                    "terrestrial_transit_time_hours": 6.5,
                    "terrestrial_cost_per_ton": 0.085,
                    "specializations": ["cement"]
                },
                "cali": {
                    "name": "Planta Cali",
                    "location": "Cali, Colombia",
                    "capacity_tonnes_per_day": 1200,
                    "available_capacity": 3000,
                    "distance_to_cartagena_km": 350,
                    "terrestrial_transit_time_hours": 5.2,
                    "terrestrial_cost_per_ton": 0.075,
                    "specializations": ["cement", "concrete"]
                }
            },
            "ports": {
                "cartagena": {
                    "name": "Puerto Cartagena",
                    "country": "Colombia",
                    "loading_capacity_tonnes_per_day": 2000,
                    "maritime_transit_time_days": 8,
                    "maritime_cost_per_ton": 4.5,
                    "destination_ports": ["mobile", "miami", "houston"]
                },
                "mobile": {
                    "name": "Mobile, Alabama",
                    "country": "USA",
                    "unloading_capacity_tonnes_per_day": 3000,
                    "final_delivery_time_hours": 4,
                    "final_delivery_cost_per_ton": 0.05
                }
            },
            "transport_modes": {
                "terrestrial": {
                    "capacity_per_truck": 35,
                    "max_trucks_per_day": 50,
                    "operating_hours": "06:00-22:00"
                },
                "maritime": {
                    "capacity_per_vessel": 8000,
                    "vessels_available": 3,
                    "operating_days": "daily"
                }
            },
            "constraints": {
                "max_terrestrial_capacity_per_day": 1750,  # 50 trucks * 35 tons
                "max_maritime_capacity_per_day": 2000,
                "min_lead_time_days": 3,
                "max_total_cost_per_ton": 6.0
            }
        }
    
    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una consulta específica de planificación inversa.
        
        Args:
            query: Diccionario con los parámetros de la consulta
            
        Returns:
            Diccionario con el resultado de la consulta
        """
        query_type = query.get("query_type")
        self.logger.info(f"Ejecutando consulta de planificación inversa: {query_type}")
        
        try:
            if query_type == "plan_from_demand":
                return self._plan_from_demand(query)
            elif query_type == "optimize_origin_selection":
                return self._optimize_origin_selection(query)
            elif query_type == "calculate_backward_schedule":
                return self._calculate_backward_schedule(query)
            elif query_type == "analyze_capacity_constraints":
                return self._analyze_capacity_constraints(query)
            elif query_type == "optimize_multimodal_flow":
                return self._optimize_multimodal_flow(query)
            elif query_type == "validate_feasibility":
                return self._validate_feasibility(query)
            else:
                raise ToolError(f"Tipo de consulta no soportado: {query_type}")
                
        except Exception as e:
            self.logger.error(f"Error ejecutando consulta de planificación inversa: {e}")
            raise ToolError(f"Error en planificación inversa: {e}")
    
    def _plan_from_demand(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Planifica hacia atrás desde la demanda final."""
        final_destination = query.get("final_destination", "").lower()
        required_quantity = query.get("required_quantity", 0)
        delivery_deadline = query.get("delivery_deadline", "")
        cargo_type = query.get("cargo_type", "cement")
        
        if not delivery_deadline:
            delivery_deadline = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        
        delivery_date = datetime.strptime(delivery_deadline, "%Y-%m-%d")
        
        # Calcular fechas hacia atrás
        maritime_arrival_date = delivery_date - timedelta(days=1)  # 1 día para descarga y entrega final
        maritime_departure_date = maritime_arrival_date - timedelta(days=8)  # 8 días de tránsito marítimo
        terrestrial_completion_date = maritime_departure_date - timedelta(days=2)  # 2 días para carga marítima
        
        # Determinar plantas de origen óptimas
        origin_recommendations = []
        total_allocated = 0
        
        for plant_id, plant_data in self._planning_data["plants"].items():
            if cargo_type in plant_data["specializations"]:
                # Calcular capacidad disponible
                available_capacity = min(plant_data["available_capacity"], required_quantity - total_allocated)
                
                if available_capacity > 0:
                    # Calcular fecha de inicio terrestre
                    terrestrial_start_date = terrestrial_completion_date - timedelta(
                        days=available_capacity / plant_data["capacity_tonnes_per_day"]
                    )
                    
                    origin_recommendations.append({
                        "plant_id": plant_id,
                        "plant_name": plant_data["name"],
                        "allocated_quantity": available_capacity,
                        "start_date": terrestrial_start_date.strftime("%Y-%m-%d"),
                        "terrestrial_cost": available_capacity * plant_data["terrestrial_cost_per_ton"],
                        "terrestrial_time_hours": plant_data["terrestrial_transit_time_hours"],
                        "capacity_utilization": (available_capacity / plant_data["capacity_tonnes_per_day"]) * 100
                    })
                    
                    total_allocated += available_capacity
                    
                    if total_allocated >= required_quantity:
                        break
        
        # Calcular costos totales estimados
        total_terrestrial_cost = sum(rec["terrestrial_cost"] for rec in origin_recommendations)
        total_maritime_cost = required_quantity * self._planning_data["ports"]["cartagena"]["maritime_cost_per_ton"]
        total_final_delivery_cost = required_quantity * self._planning_data["ports"]["mobile"]["final_delivery_cost_per_ton"]
        total_estimated_cost = total_terrestrial_cost + total_maritime_cost + total_final_delivery_cost
        
        return {
            "query_type": "plan_from_demand",
            "result": {
                "final_destination": final_destination,
                "required_quantity": required_quantity,
                "delivery_deadline": delivery_deadline,
                "cargo_type": cargo_type,
                "reverse_schedule": {
                    "delivery_date": delivery_deadline,
                    "maritime_arrival_date": maritime_arrival_date.strftime("%Y-%m-%d"),
                    "maritime_departure_date": maritime_departure_date.strftime("%Y-%m-%d"),
                    "terrestrial_completion_date": terrestrial_completion_date.strftime("%Y-%m-%d")
                },
                "origin_recommendations": origin_recommendations,
                "total_allocated": total_allocated,
                "allocation_success": total_allocated >= required_quantity,
                "cost_breakdown": {
                    "terrestrial_cost": total_terrestrial_cost,
                    "maritime_cost": total_maritime_cost,
                    "final_delivery_cost": total_final_delivery_cost,
                    "total_cost": total_estimated_cost,
                    "cost_per_ton": total_estimated_cost / required_quantity
                },
                "feasibility_analysis": {
                    "time_feasible": terrestrial_completion_date >= datetime.now() + timedelta(days=3),
                    "capacity_feasible": total_allocated >= required_quantity,
                    "cost_feasible": (total_estimated_cost / required_quantity) <= self._planning_data["constraints"]["max_total_cost_per_ton"]
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _optimize_origin_selection(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza la selección de puntos de origen."""
        required_quantity = query.get("required_quantity", 0)
        available_origins = query.get("available_origins", ["bogota", "medellin", "cali"])
        optimization_criteria = query.get("optimization_criteria", ["cost", "time", "capacity"])
        
        # Evaluar cada origen disponible
        origin_evaluations = []
        
        for origin_id in available_origins:
            if origin_id in self._planning_data["plants"]:
                plant_data = self._planning_data["plants"][origin_id]
                
                # Calcular métricas de evaluación
                cost_score = 1.0 - (plant_data["terrestrial_cost_per_ton"] / 0.1)  # Normalizar costo
                time_score = 1.0 - (plant_data["terrestrial_transit_time_hours"] / 10.0)  # Normalizar tiempo
                capacity_score = min(1.0, plant_data["available_capacity"] / required_quantity)
                
                # Calcular score compuesto
                weights = {"cost": 0.4, "time": 0.3, "capacity": 0.3}
                composite_score = (cost_score * weights["cost"] + 
                                 time_score * weights["time"] + 
                                 capacity_score * weights["capacity"])
                
                origin_evaluations.append({
                    "origin_id": origin_id,
                    "plant_name": plant_data["name"],
                    "available_capacity": plant_data["available_capacity"],
                    "terrestrial_cost_per_ton": plant_data["terrestrial_cost_per_ton"],
                    "terrestrial_time_hours": plant_data["terrestrial_transit_time_hours"],
                    "evaluation_scores": {
                        "cost_score": cost_score,
                        "time_score": time_score,
                        "capacity_score": capacity_score,
                        "composite_score": composite_score
                    },
                    "can_fulfill_demand": plant_data["available_capacity"] >= required_quantity
                })
        
        # Ordenar por score compuesto
        origin_evaluations.sort(key=lambda x: x["evaluation_scores"]["composite_score"], reverse=True)
        
        # Generar recomendaciones
        recommendations = {
            "best_single_origin": origin_evaluations[0] if origin_evaluations else None,
            "multi_origin_strategy": self._generate_multi_origin_strategy(origin_evaluations, required_quantity),
            "optimization_summary": {
                "total_origins_evaluated": len(origin_evaluations),
                "feasible_origins": len([o for o in origin_evaluations if o["can_fulfill_demand"]]),
                "optimization_criteria": optimization_criteria
            }
        }
        
        return {
            "query_type": "optimize_origin_selection",
            "result": {
                "required_quantity": required_quantity,
                "available_origins": available_origins,
                "origin_evaluations": origin_evaluations,
                "recommendations": recommendations
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_backward_schedule(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula el cronograma hacia atrás desde la entrega final."""
        delivery_deadline = query.get("delivery_deadline", "")
        required_quantity = query.get("required_quantity", 0)
        transport_modes = query.get("transport_modes", ["terrestrial", "maritime"])
        
        if not delivery_deadline:
            delivery_deadline = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        
        delivery_date = datetime.strptime(delivery_deadline, "%Y-%m-%d")
        
        # Calcular cronograma hacia atrás
        schedule = {}
        current_date = delivery_date
        
        # Fase 4: Entrega final (terrestre local)
        if "terrestrial_local" in transport_modes:
            final_delivery_time = required_quantity / self._planning_data["ports"]["mobile"]["unloading_capacity_tonnes_per_day"]
            schedule["final_delivery"] = {
                "phase": "Final Delivery",
                "start_date": (current_date - timedelta(days=final_delivery_time)).strftime("%Y-%m-%d"),
                "end_date": delivery_deadline,
                "duration_days": final_delivery_time,
                "quantity": required_quantity,
                "location": "Mobile, Alabama"
            }
            current_date = current_date - timedelta(days=final_delivery_time)
        
        # Fase 3: Descarga marítima
        if "maritime" in transport_modes:
            maritime_unloading_time = required_quantity / self._planning_data["ports"]["mobile"]["unloading_capacity_tonnes_per_day"]
            schedule["maritime_unloading"] = {
                "phase": "Maritime Unloading",
                "start_date": (current_date - timedelta(days=maritime_unloading_time)).strftime("%Y-%m-%d"),
                "end_date": current_date.strftime("%Y-%m-%d"),
                "duration_days": maritime_unloading_time,
                "quantity": required_quantity,
                "location": "Mobile, Alabama"
            }
            current_date = current_date - timedelta(days=maritime_unloading_time)
        
        # Fase 2: Tránsito marítimo
        if "maritime" in transport_modes:
            maritime_transit_days = self._planning_data["ports"]["cartagena"]["maritime_transit_time_days"]
            schedule["maritime_transit"] = {
                "phase": "Maritime Transit",
                "start_date": (current_date - timedelta(days=maritime_transit_days)).strftime("%Y-%m-%d"),
                "end_date": current_date.strftime("%Y-%m-%d"),
                "duration_days": maritime_transit_days,
                "quantity": required_quantity,
                "route": "Cartagena - Mobile, Alabama"
            }
            current_date = current_date - timedelta(days=maritime_transit_days)
        
        # Fase 1: Carga marítima
        if "maritime" in transport_modes:
            maritime_loading_time = required_quantity / self._planning_data["ports"]["cartagena"]["loading_capacity_tonnes_per_day"]
            schedule["maritime_loading"] = {
                "phase": "Maritime Loading",
                "start_date": (current_date - timedelta(days=maritime_loading_time)).strftime("%Y-%m-%d"),
                "end_date": current_date.strftime("%Y-%m-%d"),
                "duration_days": maritime_loading_time,
                "quantity": required_quantity,
                "location": "Puerto Cartagena"
            }
            current_date = current_date - timedelta(days=maritime_loading_time)
        
        # Fase 0: Transporte terrestre
        if "terrestrial" in transport_modes:
            # Calcular tiempo terrestre basado en capacidad diaria
            terrestrial_capacity_per_day = self._planning_data["constraints"]["max_terrestrial_capacity_per_day"]
            terrestrial_time_days = required_quantity / terrestrial_capacity_per_day
            
            schedule["terrestrial_transport"] = {
                "phase": "Terrestrial Transport",
                "start_date": (current_date - timedelta(days=terrestrial_time_days)).strftime("%Y-%m-%d"),
                "end_date": current_date.strftime("%Y-%m-%d"),
                "duration_days": terrestrial_time_days,
                "quantity": required_quantity,
                "route": "Plants - Puerto Cartagena"
            }
            current_date = current_date - timedelta(days=terrestrial_time_days)
        
        # Calcular tiempo total y fechas críticas
        total_duration_days = (delivery_date - current_date).days
        earliest_start_date = current_date.strftime("%Y-%m-%d")
        
        return {
            "query_type": "calculate_backward_schedule",
            "result": {
                "delivery_deadline": delivery_deadline,
                "required_quantity": required_quantity,
                "transport_modes": transport_modes,
                "backward_schedule": schedule,
                "timeline_summary": {
                    "earliest_start_date": earliest_start_date,
                    "total_duration_days": total_duration_days,
                    "critical_path": list(schedule.keys()),
                    "buffer_days": max(0, (datetime.now() - current_date).days)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_capacity_constraints(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las restricciones de capacidad en la cadena multimodal."""
        required_quantity = query.get("required_quantity", 0)
        analysis_period_days = query.get("analysis_period_days", 30)
        
        # Analizar restricciones por fase
        capacity_analysis = {
            "terrestrial_capacity": {
                "max_daily_capacity": self._planning_data["constraints"]["max_terrestrial_capacity_per_day"],
                "required_days": required_quantity / self._planning_data["constraints"]["max_terrestrial_capacity_per_day"],
                "capacity_utilization": min(100, (required_quantity / (self._planning_data["constraints"]["max_terrestrial_capacity_per_day"] * analysis_period_days)) * 100),
                "bottleneck_risk": "high" if required_quantity > self._planning_data["constraints"]["max_terrestrial_capacity_per_day"] * analysis_period_days else "low"
            },
            "maritime_capacity": {
                "max_daily_capacity": self._planning_data["constraints"]["max_maritime_capacity_per_day"],
                "required_days": required_quantity / self._planning_data["constraints"]["max_maritime_capacity_per_day"],
                "capacity_utilization": min(100, (required_quantity / (self._planning_data["constraints"]["max_maritime_capacity_per_day"] * analysis_period_days)) * 100),
                "bottleneck_risk": "high" if required_quantity > self._planning_data["constraints"]["max_maritime_capacity_per_day"] * analysis_period_days else "low"
            },
            "plant_capacity": {
                "total_available_capacity": sum(plant["available_capacity"] for plant in self._planning_data["plants"].values()),
                "required_capacity": required_quantity,
                "capacity_sufficiency": required_quantity <= sum(plant["available_capacity"] for plant in self._planning_data["plants"].values()),
                "plant_utilization": {}
            }
        }
        
        # Analizar utilización por planta
        for plant_id, plant_data in self._planning_data["plants"].items():
            capacity_analysis["plant_capacity"]["plant_utilization"][plant_id] = {
                "available_capacity": plant_data["available_capacity"],
                "daily_capacity": plant_data["capacity_tonnes_per_day"],
                "utilization_rate": min(100, (required_quantity / plant_data["available_capacity"]) * 100) if plant_data["available_capacity"] > 0 else 0
            }
        
        # Identificar cuellos de botella
        bottlenecks = []
        if capacity_analysis["terrestrial_capacity"]["bottleneck_risk"] == "high":
            bottlenecks.append("Transporte terrestre")
        if capacity_analysis["maritime_capacity"]["bottleneck_risk"] == "high":
            bottlenecks.append("Transporte marítimo")
        if not capacity_analysis["plant_capacity"]["capacity_sufficiency"]:
            bottlenecks.append("Capacidad de plantas")
        
        return {
            "query_type": "analyze_capacity_constraints",
            "result": {
                "required_quantity": required_quantity,
                "analysis_period_days": analysis_period_days,
                "capacity_analysis": capacity_analysis,
                "bottlenecks": bottlenecks,
                "recommendations": self._generate_capacity_recommendations(capacity_analysis, bottlenecks)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _optimize_multimodal_flow(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza el flujo multimodal completo."""
        required_quantity = query.get("required_quantity", 0)
        delivery_deadline = query.get("delivery_deadline", "")
        optimization_objectives = query.get("optimization_objectives", ["minimize_cost", "minimize_time"])
        
        if not delivery_deadline:
            delivery_deadline = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        
        # Generar múltiples escenarios de optimización
        scenarios = []
        
        # Escenario 1: Minimizar costo
        if "minimize_cost" in optimization_objectives:
            cost_optimized = self._generate_cost_optimized_scenario(required_quantity, delivery_deadline)
            scenarios.append(cost_optimized)
        
        # Escenario 2: Minimizar tiempo
        if "minimize_time" in optimization_objectives:
            time_optimized = self._generate_time_optimized_scenario(required_quantity, delivery_deadline)
            scenarios.append(time_optimized)
        
        # Escenario 3: Balanceado
        balanced = self._generate_balanced_scenario(required_quantity, delivery_deadline)
        scenarios.append(balanced)
        
        # Evaluar y rankear escenarios
        ranked_scenarios = self._rank_scenarios(scenarios, optimization_objectives)
        
        return {
            "query_type": "optimize_multimodal_flow",
            "result": {
                "required_quantity": required_quantity,
                "delivery_deadline": delivery_deadline,
                "optimization_objectives": optimization_objectives,
                "scenarios": ranked_scenarios,
                "recommended_scenario": ranked_scenarios[0] if ranked_scenarios else None,
                "optimization_summary": {
                    "total_scenarios": len(scenarios),
                    "feasible_scenarios": len([s for s in scenarios if s["feasible"]]),
                    "best_cost": min(s["total_cost"] for s in scenarios if s["feasible"]) if scenarios else 0,
                    "best_time": min(s["total_time_days"] for s in scenarios if s["feasible"]) if scenarios else 0
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _validate_feasibility(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Valida la factibilidad de un plan multimodal."""
        required_quantity = query.get("required_quantity", 0)
        delivery_deadline = query.get("delivery_deadline", "")
        max_cost_per_ton = query.get("max_cost_per_ton", 6.0)
        
        if not delivery_deadline:
            delivery_deadline = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        
        delivery_date = datetime.strptime(delivery_deadline, "%Y-%m-%d")
        
        # Validaciones de factibilidad
        feasibility_checks = {
            "time_feasibility": {
                "min_required_days": 12,  # Mínimo tiempo para operación completa
                "available_days": (delivery_date - datetime.now()).days,
                "feasible": (delivery_date - datetime.now()).days >= 12,
                "message": "Tiempo suficiente disponible" if (delivery_date - datetime.now()).days >= 12 else "Tiempo insuficiente"
            },
            "capacity_feasibility": {
                "total_plant_capacity": sum(plant["available_capacity"] for plant in self._planning_data["plants"].values()),
                "required_capacity": required_quantity,
                "feasible": required_quantity <= sum(plant["available_capacity"] for plant in self._planning_data["plants"].values()),
                "message": "Capacidad suficiente disponible" if required_quantity <= sum(plant["available_capacity"] for plant in self._planning_data["plants"].values()) else "Capacidad insuficiente"
            },
            "cost_feasibility": {
                "estimated_cost_per_ton": 5.5,  # Estimación conservadora
                "max_cost_per_ton": max_cost_per_ton,
                "feasible": 5.5 <= max_cost_per_ton,
                "message": "Costo dentro del presupuesto" if 5.5 <= max_cost_per_ton else "Costo excede presupuesto"
            },
            "logistics_feasibility": {
                "terrestrial_capacity_sufficient": required_quantity <= self._planning_data["constraints"]["max_terrestrial_capacity_per_day"] * 10,
                "maritime_capacity_sufficient": required_quantity <= self._planning_data["constraints"]["max_maritime_capacity_per_day"] * 5,
                "feasible": (required_quantity <= self._planning_data["constraints"]["max_terrestrial_capacity_per_day"] * 10 and 
                           required_quantity <= self._planning_data["constraints"]["max_maritime_capacity_per_day"] * 5),
                "message": "Capacidad logística suficiente" if (required_quantity <= self._planning_data["constraints"]["max_terrestrial_capacity_per_day"] * 10 and 
                                                               required_quantity <= self._planning_data["constraints"]["max_maritime_capacity_per_day"] * 5) else "Capacidad logística insuficiente"
            }
        }
        
        # Determinar factibilidad general
        overall_feasible = all(check["feasible"] for check in feasibility_checks.values())
        
        # Generar recomendaciones
        recommendations = []
        if not feasibility_checks["time_feasibility"]["feasible"]:
            recommendations.append("Considerar extender la fecha de entrega o acelerar el inicio de operaciones")
        if not feasibility_checks["capacity_feasibility"]["feasible"]:
            recommendations.append("Aumentar capacidad de plantas o reducir cantidad requerida")
        if not feasibility_checks["cost_feasibility"]["feasible"]:
            recommendations.append("Optimizar costos o aumentar presupuesto")
        if not feasibility_checks["logistics_feasibility"]["feasible"]:
            recommendations.append("Aumentar capacidad de transporte o extender tiempo de operación")
        
        return {
            "query_type": "validate_feasibility",
            "result": {
                "required_quantity": required_quantity,
                "delivery_deadline": delivery_deadline,
                "max_cost_per_ton": max_cost_per_ton,
                "feasibility_checks": feasibility_checks,
                "overall_feasible": overall_feasible,
                "feasibility_score": sum(1 for check in feasibility_checks.values() if check["feasible"]) / len(feasibility_checks),
                "recommendations": recommendations,
                "risk_assessment": {
                    "low_risk": overall_feasible,
                    "medium_risk": not overall_feasible and sum(1 for check in feasibility_checks.values() if check["feasible"]) >= 2,
                    "high_risk": sum(1 for check in feasibility_checks.values() if check["feasible"]) < 2
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_multi_origin_strategy(self, origin_evaluations: List[Dict], required_quantity: int) -> Dict[str, Any]:
        """Genera estrategia de múltiples orígenes."""
        strategy = {
            "recommended_origins": [],
            "allocation_strategy": "proportional",
            "total_cost": 0,
            "total_time": 0
        }
        
        remaining_quantity = required_quantity
        
        for origin in origin_evaluations:
            if remaining_quantity <= 0:
                break
            
            allocated_quantity = min(origin["available_capacity"], remaining_quantity)
            strategy["recommended_origins"].append({
                "origin_id": origin["origin_id"],
                "plant_name": origin["plant_name"],
                "allocated_quantity": allocated_quantity,
                "cost": allocated_quantity * origin["terrestrial_cost_per_ton"],
                "time_hours": origin["terrestrial_time_hours"]
            })
            
            strategy["total_cost"] += allocated_quantity * origin["terrestrial_cost_per_ton"]
            strategy["total_time"] = max(strategy["total_time"], origin["terrestrial_time_hours"])
            remaining_quantity -= allocated_quantity
        
        return strategy
    
    def _generate_capacity_recommendations(self, capacity_analysis: Dict, bottlenecks: List[str]) -> List[str]:
        """Genera recomendaciones basadas en análisis de capacidad."""
        recommendations = []
        
        if "Transporte terrestre" in bottlenecks:
            recommendations.append("Aumentar flota de camiones o extender horarios de operación")
        if "Transporte marítimo" in bottlenecks:
            recommendations.append("Contratar buques adicionales o aumentar frecuencia de salidas")
        if "Capacidad de plantas" in bottlenecks:
            recommendations.append("Aumentar capacidad de producción o activar plantas adicionales")
        
        return recommendations
    
    def _generate_cost_optimized_scenario(self, quantity: int, deadline: str) -> Dict[str, Any]:
        """Genera escenario optimizado por costo."""
        return {
            "scenario_name": "Cost Optimized",
            "optimization_focus": "minimize_cost",
            "total_cost": quantity * 5.2,  # Costo optimizado
            "total_time_days": 15,
            "feasible": True,
            "description": "Escenario optimizado para minimizar costos totales"
        }
    
    def _generate_time_optimized_scenario(self, quantity: int, deadline: str) -> Dict[str, Any]:
        """Genera escenario optimizado por tiempo."""
        return {
            "scenario_name": "Time Optimized",
            "optimization_focus": "minimize_time",
            "total_cost": quantity * 6.0,  # Costo más alto por velocidad
            "total_time_days": 10,
            "feasible": True,
            "description": "Escenario optimizado para minimizar tiempo total"
        }
    
    def _generate_balanced_scenario(self, quantity: int, deadline: str) -> Dict[str, Any]:
        """Genera escenario balanceado."""
        return {
            "scenario_name": "Balanced",
            "optimization_focus": "balanced",
            "total_cost": quantity * 5.6,  # Costo balanceado
            "total_time_days": 12,
            "feasible": True,
            "description": "Escenario balanceado entre costo y tiempo"
        }
    
    def _rank_scenarios(self, scenarios: List[Dict], objectives: List[str]) -> List[Dict]:
        """Rankea escenarios basado en objetivos."""
        for scenario in scenarios:
            score = 0
            if "minimize_cost" in objectives:
                score += (1.0 - scenario["total_cost"] / max(s["total_cost"] for s in scenarios)) * 0.5
            if "minimize_time" in objectives:
                score += (1.0 - scenario["total_time_days"] / max(s["total_time_days"] for s in scenarios)) * 0.5
            
            scenario["optimization_score"] = score
        
        return sorted(scenarios, key=lambda x: x["optimization_score"], reverse=True)


def create_reverse_planning_tool() -> FunctionTool:
    """
    Crea una instancia de FunctionTool para ReversePlanningTool.
    
    Returns:
        FunctionTool configurada para uso con Google ADK
    """
    tool_instance = ReversePlanningTool()
    
    return FunctionTool(
        name=tool_instance.name,
        description=tool_instance.description,
        func=tool_instance.execute
    )
