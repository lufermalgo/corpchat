"""
Port Coordination Tool para el MaritimeLogisticsAgent.

Esta herramienta simula la coordinación con puertos para optimizar
operaciones de carga, descarga y tiempos de estadía.
"""

import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base_tool import BaseTool, FunctionTool
from ...shared.types import ToolConfig, ToolType
from ...shared.exceptions import ToolError
from ...shared.utils import get_logger


class PortCoordinationTool(BaseTool):
    """
    Herramienta para coordinación con puertos marítimos.
    
    Simula la integración con sistemas portuarios para:
    - Reserva de slots de carga/descarga
    - Coordinación de horarios
    - Optimización de tiempos de estadía
    - Gestión de recursos portuarios
    """
    
    def __init__(self):
        super().__init__(
            name="port_coordination_tool",
            description="Herramienta para coordinación con puertos marítimos",
            tool_type=ToolType.FUNCTION_TOOL,
            config=ToolConfig(
                name="port_coordination_tool",
                type=ToolType.FUNCTION_TOOL,
                description="Herramienta para coordinación con puertos marítimos",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query_type": {
                            "type": "string",
                            "enum": [
                                "reserve_loading_slot",
                                "check_port_availability",
                                "coordinate_berthing",
                                "optimize_lay_time",
                                "get_port_resources",
                                "schedule_port_operations",
                                "monitor_port_status"
                            ],
                            "description": "Tipo de consulta a realizar"
                        },
                        "port_name": {
                            "type": "string",
                            "description": "Nombre del puerto"
                        },
                        "vessel_id": {
                            "type": "string",
                            "description": "ID del buque"
                        },
                        "cargo_weight": {
                            "type": "number",
                            "description": "Peso de la carga en toneladas"
                        },
                        "arrival_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Fecha de llegada"
                        },
                        "departure_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Fecha de salida"
                        },
                        "operation_type": {
                            "type": "string",
                            "enum": ["loading", "unloading", "both"],
                            "description": "Tipo de operación"
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
        
        # Base de datos simulada de puertos
        self._port_database = {
            "ports": {
                "cartagena": {
                    "name": "Puerto Cartagena",
                    "country": "Colombia",
                    "coordinates": {"lat": 10.3910, "lon": -75.4794},
                    "capacity": {
                        "total_berths": 12,
                        "bulk_cargo_berths": 4,
                        "container_berths": 6,
                        "general_cargo_berths": 2
                    },
                    "facilities": {
                        "cement_silo": True,
                        "bulk_loading": True,
                        "container_terminal": True,
                        "rail_connection": True,
                        "warehouse_space": 50000
                    },
                    "operational_rates": {
                        "loading_rate_tonnes_per_hour": 250,
                        "unloading_rate_tonnes_per_hour": 300,
                        "crane_capacity_tonnes": 50,
                        "conveyor_capacity_tonnes_per_hour": 500
                    },
                    "costs": {
                        "berth_fee_per_hour": 150,
                        "loading_fee_per_ton": 2.5,
                        "unloading_fee_per_ton": 2.0,
                        "storage_fee_per_ton_per_day": 0.5
                    },
                    "operating_hours": {
                        "monday_to_friday": "06:00-22:00",
                        "saturday": "06:00-18:00",
                        "sunday": "08:00-16:00"
                    },
                    "restrictions": {
                        "max_vessel_length": 300,
                        "max_vessel_draft": 12,
                        "weather_limitations": "moderate"
                    }
                },
                "mobile": {
                    "name": "Mobile, Alabama",
                    "country": "USA",
                    "coordinates": {"lat": 30.6944, "lon": -88.0431},
                    "capacity": {
                        "total_berths": 20,
                        "bulk_cargo_berths": 8,
                        "container_berths": 8,
                        "general_cargo_berths": 4
                    },
                    "facilities": {
                        "cement_silo": True,
                        "bulk_unloading": True,
                        "container_terminal": True,
                        "rail_connection": True,
                        "warehouse_space": 80000
                    },
                    "operational_rates": {
                        "loading_rate_tonnes_per_hour": 400,
                        "unloading_rate_tonnes_per_hour": 450,
                        "crane_capacity_tonnes": 75,
                        "conveyor_capacity_tonnes_per_hour": 800
                    },
                    "costs": {
                        "berth_fee_per_hour": 200,
                        "loading_fee_per_ton": 3.0,
                        "unloading_fee_per_ton": 2.5,
                        "storage_fee_per_ton_per_day": 0.8
                    },
                    "operating_hours": {
                        "monday_to_friday": "24/7",
                        "saturday": "06:00-22:00",
                        "sunday": "08:00-20:00"
                    },
                    "restrictions": {
                        "max_vessel_length": 400,
                        "max_vessel_draft": 15,
                        "weather_limitations": "low"
                    }
                },
                "barranquilla": {
                    "name": "Puerto Barranquilla",
                    "country": "Colombia",
                    "coordinates": {"lat": 10.9685, "lon": -74.7813},
                    "capacity": {
                        "total_berths": 8,
                        "bulk_cargo_berths": 3,
                        "container_berths": 3,
                        "general_cargo_berths": 2
                    },
                    "facilities": {
                        "cement_silo": False,
                        "bulk_loading": True,
                        "container_terminal": True,
                        "rail_connection": False,
                        "warehouse_space": 30000
                    },
                    "operational_rates": {
                        "loading_rate_tonnes_per_hour": 180,
                        "unloading_rate_tonnes_per_hour": 220,
                        "crane_capacity_tonnes": 40,
                        "conveyor_capacity_tonnes_per_hour": 350
                    },
                    "costs": {
                        "berth_fee_per_hour": 120,
                        "loading_fee_per_ton": 2.0,
                        "unloading_fee_per_ton": 1.8,
                        "storage_fee_per_ton_per_day": 0.4
                    },
                    "operating_hours": {
                        "monday_to_friday": "06:00-20:00",
                        "saturday": "06:00-16:00",
                        "sunday": "08:00-14:00"
                    },
                    "restrictions": {
                        "max_vessel_length": 250,
                        "max_vessel_draft": 10,
                        "weather_limitations": "high"
                    }
                }
            },
            "reservations": {},
            "current_operations": {}
        }
    
    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una consulta específica de coordinación portuaria.
        
        Args:
            query: Diccionario con los parámetros de la consulta
            
        Returns:
            Diccionario con el resultado de la consulta
        """
        query_type = query.get("query_type")
        self.logger.info(f"Ejecutando consulta de coordinación portuaria: {query_type}")
        
        try:
            if query_type == "reserve_loading_slot":
                return self._reserve_loading_slot(query)
            elif query_type == "check_port_availability":
                return self._check_port_availability(query)
            elif query_type == "coordinate_berthing":
                return self._coordinate_berthing(query)
            elif query_type == "optimize_lay_time":
                return self._optimize_lay_time(query)
            elif query_type == "get_port_resources":
                return self._get_port_resources(query)
            elif query_type == "schedule_port_operations":
                return self._schedule_port_operations(query)
            elif query_type == "monitor_port_status":
                return self._monitor_port_status(query)
            else:
                raise ToolError(f"Tipo de consulta no soportado: {query_type}")
                
        except Exception as e:
            self.logger.error(f"Error ejecutando consulta de coordinación portuaria: {e}")
            raise ToolError(f"Error en coordinación portuaria: {e}")
    
    def _reserve_loading_slot(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Reserva un slot de carga en el puerto."""
        port_name = query.get("port_name", "").lower()
        vessel_id = query.get("vessel_id", "")
        cargo_weight = query.get("cargo_weight", 0)
        arrival_date = query.get("arrival_date", "")
        operation_type = query.get("operation_type", "loading")
        
        if port_name not in self._port_database["ports"]:
            raise ToolError(f"Puerto no encontrado: {port_name}")
        
        port_info = self._port_database["ports"][port_name]
        
        # Calcular tiempo de operación
        if operation_type == "loading":
            operation_hours = cargo_weight / port_info["operational_rates"]["loading_rate_tonnes_per_hour"]
        elif operation_type == "unloading":
            operation_hours = cargo_weight / port_info["operational_rates"]["unloading_rate_tonnes_per_hour"]
        else:  # both
            operation_hours = (cargo_weight / port_info["operational_rates"]["loading_rate_tonnes_per_hour"] + 
                             cargo_weight / port_info["operational_rates"]["unloading_rate_tonnes_per_hour"])
        
        # Agregar tiempo de preparación y limpieza
        total_hours = operation_hours + 4  # 4 horas adicionales
        
        # Simular disponibilidad de slots
        available_slots = random.randint(2, 6)
        slot_reservation_id = f"SLOT_{vessel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Calcular costos
        berth_cost = total_hours * port_info["costs"]["berth_fee_per_hour"]
        operation_cost = cargo_weight * port_info["costs"]["loading_fee_per_ton"]
        total_cost = berth_cost + operation_cost
        
        # Crear reserva
        reservation = {
            "reservation_id": slot_reservation_id,
            "vessel_id": vessel_id,
            "port_name": port_info["name"],
            "operation_type": operation_type,
            "cargo_weight": cargo_weight,
            "arrival_date": arrival_date,
            "estimated_operation_hours": round(total_hours, 2),
            "cost_breakdown": {
                "berth_cost": berth_cost,
                "operation_cost": operation_cost,
                "total_cost": total_cost
            },
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        self._port_database["reservations"][slot_reservation_id] = reservation
        
        return {
            "query_type": "reserve_loading_slot",
            "result": {
                "reservation": reservation,
                "available_slots": available_slots,
                "estimated_completion": (datetime.now() + timedelta(hours=total_hours)).isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_port_availability(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica disponibilidad del puerto en un período específico."""
        port_name = query.get("port_name", "").lower()
        arrival_date = query.get("arrival_date", "")
        departure_date = query.get("departure_date", "")
        
        if port_name not in self._port_database["ports"]:
            raise ToolError(f"Puerto no encontrado: {port_name}")
        
        port_info = self._port_database["ports"][port_name]
        
        # Simular disponibilidad de berths
        total_berths = port_info["capacity"]["total_berths"]
        occupied_berths = random.randint(2, total_berths - 2)
        available_berths = total_berths - occupied_berths
        
        # Simular horarios disponibles
        available_slots = []
        current_time = datetime.now()
        for i in range(7):  # Próximos 7 días
            slot_date = current_time + timedelta(days=i)
            available_slots.append({
                "date": slot_date.strftime("%Y-%m-%d"),
                "available_berths": random.randint(1, available_berths),
                "operating_hours": port_info["operating_hours"],
                "weather_conditions": random.choice(["good", "moderate", "poor"])
            })
        
        return {
            "query_type": "check_port_availability",
            "result": {
                "port_name": port_info["name"],
                "total_berths": total_berths,
                "available_berths": available_berths,
                "occupied_berths": occupied_berths,
                "availability_slots": available_slots,
                "operating_hours": port_info["operating_hours"],
                "facilities": port_info["facilities"]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _coordinate_berthing(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Coordina el atraque del buque."""
        port_name = query.get("port_name", "").lower()
        vessel_id = query.get("vessel_id", "")
        arrival_date = query.get("arrival_date", "")
        
        if port_name not in self._port_database["ports"]:
            raise ToolError(f"Puerto no encontrado: {port_name}")
        
        port_info = self._port_database["ports"][port_name]
        
        # Simular asignación de berth
        available_berths = [f"Berth_{i+1}" for i in range(port_info["capacity"]["total_berths"])]
        assigned_berth = random.choice(available_berths)
        
        # Simular tiempo de espera
        waiting_time_hours = random.randint(0, 6)
        
        # Calcular tiempo de atraque
        berthing_time = datetime.now() + timedelta(hours=waiting_time_hours)
        
        berthing_coordination = {
            "vessel_id": vessel_id,
            "port_name": port_info["name"],
            "assigned_berth": assigned_berth,
            "arrival_time": arrival_date,
            "berthing_time": berthing_time.isoformat(),
            "waiting_time_hours": waiting_time_hours,
            "pilot_required": True,
            "tug_assistance": True,
            "berthing_fee": port_info["costs"]["berth_fee_per_hour"] * 2  # 2 horas de berthing
        }
        
        return {
            "query_type": "coordinate_berthing",
            "result": {
                "berthing_coordination": berthing_coordination,
                "port_restrictions": port_info["restrictions"],
                "operational_guidelines": [
                    "Presentar documentación 24 horas antes",
                    "Confirmar llegada 2 horas antes",
                    "Mantener comunicación con torre de control"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _optimize_lay_time(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza el tiempo de estadía en puerto."""
        port_name = query.get("port_name", "").lower()
        cargo_weight = query.get("cargo_weight", 0)
        operation_type = query.get("operation_type", "loading")
        
        if port_name not in self._port_database["ports"]:
            raise ToolError(f"Puerto no encontrado: {port_name}")
        
        port_info = self._port_database["ports"][port_name]
        
        # Calcular tiempo mínimo de operación
        if operation_type == "loading":
            min_operation_hours = cargo_weight / port_info["operational_rates"]["loading_rate_tonnes_per_hour"]
        elif operation_type == "unloading":
            min_operation_hours = cargo_weight / port_info["operational_rates"]["unloading_rate_tonnes_per_hour"]
        else:  # both
            min_operation_hours = (cargo_weight / port_info["operational_rates"]["loading_rate_tonnes_per_hour"] + 
                                 cargo_weight / port_info["operational_rates"]["unloading_rate_tonnes_per_hour"])
        
        # Tiempo adicional para preparación, documentación, etc.
        preparation_hours = 2
        documentation_hours = 1
        cleaning_hours = 1
        
        total_minimum_hours = min_operation_hours + preparation_hours + documentation_hours + cleaning_hours
        
        # Simular optimizaciones disponibles
        optimizations = []
        if port_info["facilities"]["rail_connection"]:
            optimizations.append({
                "type": "rail_connection",
                "description": "Conexión directa a ferrocarril",
                "time_savings_hours": 2,
                "cost_impact": 0
            })
        
        if port_info["facilities"]["cement_silo"]:
            optimizations.append({
                "type": "cement_silo",
                "description": "Silo de cemento automatizado",
                "time_savings_hours": 4,
                "cost_impact": 0.1  # 10% más caro pero más rápido
            })
        
        # Calcular tiempo optimizado
        optimization_savings = sum(opt["time_savings_hours"] for opt in optimizations)
        optimized_hours = max(total_minimum_hours - optimization_savings, total_minimum_hours * 0.8)
        
        return {
            "query_type": "optimize_lay_time",
            "result": {
                "port_name": port_info["name"],
                "cargo_weight": cargo_weight,
                "operation_type": operation_type,
                "lay_time_analysis": {
                    "minimum_hours": round(total_minimum_hours, 2),
                    "optimized_hours": round(optimized_hours, 2),
                    "time_savings_hours": round(total_minimum_hours - optimized_hours, 2),
                    "optimization_percentage": round(((total_minimum_hours - optimized_hours) / total_minimum_hours) * 100, 1)
                },
                "available_optimizations": optimizations,
                "operational_rates": port_info["operational_rates"]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_port_resources(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene información sobre recursos disponibles en el puerto."""
        port_name = query.get("port_name", "").lower()
        
        if port_name not in self._port_database["ports"]:
            raise ToolError(f"Puerto no encontrado: {port_name}")
        
        port_info = self._port_database["ports"][port_name]
        
        # Simular estado de recursos
        resources = {
            "cranes": {
                "total": 8,
                "available": random.randint(5, 8),
                "capacity_tonnes": port_info["operational_rates"]["crane_capacity_tonnes"]
            },
            "conveyors": {
                "total": 12,
                "available": random.randint(8, 12),
                "capacity_tonnes_per_hour": port_info["operational_rates"]["conveyor_capacity_tonnes_per_hour"]
            },
            "storage": {
                "total_capacity": port_info["facilities"]["warehouse_space"],
                "available_capacity": random.randint(10000, port_info["facilities"]["warehouse_space"]),
                "utilization_rate": random.uniform(0.3, 0.8)
            },
            "personnel": {
                "dock_workers": random.randint(20, 40),
                "crane_operators": random.randint(8, 12),
                "supervisors": random.randint(3, 6)
            }
        }
        
        return {
            "query_type": "get_port_resources",
            "result": {
                "port_name": port_info["name"],
                "resources": resources,
                "facilities": port_info["facilities"],
                "operational_capacity": {
                    "max_loading_rate": port_info["operational_rates"]["loading_rate_tonnes_per_hour"],
                    "max_unloading_rate": port_info["operational_rates"]["unloading_rate_tonnes_per_hour"]
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _schedule_port_operations(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Programa operaciones portuarias."""
        port_name = query.get("port_name", "").lower()
        vessel_id = query.get("vessel_id", "")
        cargo_weight = query.get("cargo_weight", 0)
        operation_type = query.get("operation_type", "loading")
        
        if port_name not in self._port_database["ports"]:
            raise ToolError(f"Puerto no encontrado: {port_name}")
        
        port_info = self._port_database["ports"][port_name]
        
        # Crear horario de operaciones
        operation_schedule = []
        current_time = datetime.now()
        
        # Preparación
        operation_schedule.append({
            "phase": "preparation",
            "start_time": current_time.isoformat(),
            "duration_hours": 2,
            "description": "Preparación del buque y equipos",
            "resources_required": ["dock_workers", "supervisors"]
        })
        
        # Operación principal
        if operation_type == "loading":
            operation_hours = cargo_weight / port_info["operational_rates"]["loading_rate_tonnes_per_hour"]
            operation_description = f"Carga de {cargo_weight} toneladas"
        elif operation_type == "unloading":
            operation_hours = cargo_weight / port_info["operational_rates"]["unloading_rate_tonnes_per_hour"]
            operation_description = f"Descarga de {cargo_weight} toneladas"
        else:
            operation_hours = (cargo_weight / port_info["operational_rates"]["loading_rate_tonnes_per_hour"] + 
                             cargo_weight / port_info["operational_rates"]["unloading_rate_tonnes_per_hour"])
            operation_description = f"Carga y descarga de {cargo_weight} toneladas"
        
        operation_schedule.append({
            "phase": "main_operation",
            "start_time": (current_time + timedelta(hours=2)).isoformat(),
            "duration_hours": round(operation_hours, 2),
            "description": operation_description,
            "resources_required": ["cranes", "conveyors", "dock_workers", "crane_operators"]
        })
        
        # Finalización
        operation_schedule.append({
            "phase": "completion",
            "start_time": (current_time + timedelta(hours=2 + operation_hours)).isoformat(),
            "duration_hours": 1,
            "description": "Limpieza y documentación final",
            "resources_required": ["dock_workers", "supervisors"]
        })
        
        total_duration = 2 + operation_hours + 1
        
        return {
            "query_type": "schedule_port_operations",
            "result": {
                "vessel_id": vessel_id,
                "port_name": port_info["name"],
                "operation_type": operation_type,
                "cargo_weight": cargo_weight,
                "operation_schedule": operation_schedule,
                "total_duration_hours": round(total_duration, 2),
                "estimated_completion": (current_time + timedelta(hours=total_duration)).isoformat(),
                "resource_requirements": {
                    "cranes_needed": min(2, cargo_weight // 1000),
                    "workers_needed": min(10, cargo_weight // 500),
                    "supervisors_needed": 2
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _monitor_port_status(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Monitorea el estado actual del puerto."""
        port_name = query.get("port_name", "").lower()
        
        if port_name not in self._port_database["ports"]:
            raise ToolError(f"Puerto no encontrado: {port_name}")
        
        port_info = self._port_database["ports"][port_name]
        
        # Simular estado actual
        current_operations = random.randint(2, 6)
        total_berths = port_info["capacity"]["total_berths"]
        utilization_rate = (current_operations / total_berths) * 100
        
        # Simular condiciones operativas
        weather_conditions = random.choice(["excellent", "good", "moderate", "poor"])
        congestion_level = random.choice(["low", "medium", "high"])
        
        port_status = {
            "port_name": port_info["name"],
            "current_operations": current_operations,
            "total_berths": total_berths,
            "utilization_rate": round(utilization_rate, 1),
            "weather_conditions": weather_conditions,
            "congestion_level": congestion_level,
            "operational_status": "normal" if utilization_rate < 80 else "busy",
            "next_available_slot": (datetime.now() + timedelta(hours=random.randint(2, 8))).isoformat(),
            "active_vessels": [
                f"Vessel_{i+1}" for i in range(current_operations)
            ]
        }
        
        return {
            "query_type": "monitor_port_status",
            "result": {
                "port_status": port_status,
                "operational_hours": port_info["operating_hours"],
                "facilities_status": {
                    "cranes_operational": random.randint(6, 8),
                    "conveyors_operational": random.randint(10, 12),
                    "storage_available": random.randint(15000, 50000)
                }
            },
            "timestamp": datetime.now().isoformat()
        }


def create_port_coordination_tool() -> FunctionTool:
    """
    Crea una instancia de FunctionTool para PortCoordinationTool.
    
    Returns:
        FunctionTool configurada para uso con Google ADK
    """
    tool_instance = PortCoordinationTool()
    
    return FunctionTool(
        name=tool_instance.name,
        description=tool_instance.description,
        func=tool_instance.execute
    )
