"""
MaritimeLogisticsAgent para el Core Cognitivo.

Este agente especializado maneja todas las operaciones relacionadas con
transporte marítimo, incluyendo selección de buques, coordinación portuaria
y optimización de rutas marítimas.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..agents.base_agent import BaseAgent
from ...shared.types import AgentConfig, AgentSkill, ToolConfig, AgentType, ToolType
from ...shared.exceptions import AgentError
from ...shared.utils import get_logger
from ..tools.maritime import (
    MaritimePartnerTool, create_maritime_partner_tool,
    VesselSelectionTool, create_vessel_selection_tool,
    PortCoordinationTool, create_port_coordination_tool
)


class MaritimeLogisticsAgent(BaseAgent):
    """
    Agente especializado en logística marítima.
    
    Este agente utiliza herramientas especializadas para:
    - Selección inteligente de buques
    - Coordinación con puertos
    - Cálculo de fletes y costos
    - Optimización de rutas marítimas
    - Análisis de tiempos de estadía
    """
    
    def __init__(self, config: AgentConfig):
        """
        Inicializa el MaritimeLogisticsAgent.
        
        Args:
            config: Configuración del agente
        """
        super().__init__(config)
        self.logger = get_logger(f"Agent.{self.name}")
        
        # Inicializar herramientas marítimas
        self._initialize_maritime_tools()
        
        self.logger.info(f"MaritimeLogisticsAgent '{self.name}' inicializado correctamente")
    
    def _initialize_maritime_tools(self):
        """Inicializa las herramientas marítimas especializadas."""
        try:
            # Crear herramientas marítimas
            self.maritime_partner_tool = create_maritime_partner_tool()
            self.vessel_selection_tool = create_vessel_selection_tool()
            self.port_coordination_tool = create_port_coordination_tool()
            
            self.logger.info("Herramientas marítimas inicializadas correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando herramientas marítimas: {e}")
            raise AgentError(f"Error inicializando herramientas marítimas: {e}")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Procesa una consulta relacionada con logística marítima.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Diccionario con la respuesta del agente
        """
        self.logger.info(f"Procesando consulta marítima: {query}")
        
        try:
            # Analizar tipo de consulta
            query_type = self._analyze_query_type(query)
            
            # Procesar según el tipo de consulta
            if query_type == "vessel_selection":
                return self._handle_vessel_selection(query)
            elif query_type == "port_coordination":
                return self._handle_port_coordination(query)
            elif query_type == "freight_calculation":
                return self._handle_freight_calculation(query)
            elif query_type == "route_optimization":
                return self._handle_route_optimization(query)
            elif query_type == "lay_time_analysis":
                return self._handle_lay_time_analysis(query)
            elif query_type == "port_availability":
                return self._handle_port_availability(query)
            else:
                return self._handle_general_query(query)
                
        except Exception as e:
            self.logger.error(f"Error procesando consulta marítima: {e}")
            return {
                "agent": self.name,
                "query_type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def execute_skill(self, skill_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una skill específica del agente.
        
        Args:
            skill_id: ID de la skill a ejecutar
            parameters: Parámetros para la skill
            
        Returns:
            Diccionario con el resultado de la skill
        """
        self.logger.info(f"Ejecutando skill marítima: {skill_id}")
        
        try:
            if skill_id == "plan_maritime_transport":
                return self._execute_plan_maritime_transport(parameters)
            elif skill_id == "select_vessel":
                return self._execute_select_vessel(parameters)
            elif skill_id == "coordinate_port_operations":
                return self._execute_coordinate_port_operations(parameters)
            elif skill_id == "calculate_maritime_costs":
                return self._execute_calculate_maritime_costs(parameters)
            elif skill_id == "optimize_maritime_route":
                return self._execute_optimize_maritime_route(parameters)
            else:
                raise AgentError(f"Skill no soportada: {skill_id}")
                
        except Exception as e:
            self.logger.error(f"Error ejecutando skill marítima: {e}")
            raise AgentError(f"Error ejecutando skill marítima: {e}")
    
    def _analyze_query_type(self, query: str) -> str:
        """Analiza el tipo de consulta marítima."""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["buque", "vessel", "embarcación", "seleccionar"]):
            return "vessel_selection"
        elif any(keyword in query_lower for keyword in ["puerto", "port", "coordinación", "atraque"]):
            return "port_coordination"
        elif any(keyword in query_lower for keyword in ["flete", "freight", "costo", "precio"]):
            return "freight_calculation"
        elif any(keyword in query_lower for keyword in ["ruta", "route", "optimizar", "distancia"]):
            return "route_optimization"
        elif any(keyword in query_lower for keyword in ["estadía", "lay time", "tiempo puerto"]):
            return "lay_time_analysis"
        elif any(keyword in query_lower for keyword in ["disponibilidad", "availability", "horarios"]):
            return "port_availability"
        else:
            return "general"
    
    def _handle_vessel_selection(self, query: str) -> Dict[str, Any]:
        """Maneja consultas de selección de buques."""
        # Extraer parámetros de la consulta
        cargo_weight = self._extract_cargo_weight(query)
        origin_port = self._extract_origin_port(query)
        destination_port = self._extract_destination_port(query)
        
        # Ejecutar selección de buques
        vessel_result = self.vessel_selection_tool.run({
            "query_type": "select_optimal_vessel",
            "cargo_weight": cargo_weight,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "priority_criteria": ["cost", "speed"]
        })
        
        return {
            "agent": self.name,
            "query_type": "vessel_selection",
            "analysis": f"Análisis de selección de buques para {cargo_weight} toneladas desde {origin_port} hasta {destination_port}",
            "result": vessel_result,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_port_coordination(self, query: str) -> Dict[str, Any]:
        """Maneja consultas de coordinación portuaria."""
        port_name = self._extract_port_name(query)
        
        # Verificar disponibilidad del puerto
        availability_result = self.port_coordination_tool.run({
            "query_type": "check_port_availability",
            "port_name": port_name
        })
        
        return {
            "agent": self.name,
            "query_type": "port_coordination",
            "analysis": f"Coordinación con {port_name} para operaciones marítimas",
            "result": availability_result,
            "confidence": 0.90,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_freight_calculation(self, query: str) -> Dict[str, Any]:
        """Maneja consultas de cálculo de fletes."""
        cargo_weight = self._extract_cargo_weight(query)
        origin_port = self._extract_origin_port(query)
        destination_port = self._extract_destination_port(query)
        
        # Calcular flete
        freight_result = self.maritime_partner_tool.run({
            "query_type": "calculate_freight",
            "origin_port": origin_port,
            "destination_port": destination_port,
            "cargo_weight": cargo_weight
        })
        
        return {
            "agent": self.name,
            "query_type": "freight_calculation",
            "analysis": f"Cálculo de flete para {cargo_weight} toneladas desde {origin_port} hasta {destination_port}",
            "result": freight_result,
            "confidence": 0.92,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_route_optimization(self, query: str) -> Dict[str, Any]:
        """Maneja consultas de optimización de rutas."""
        origin_port = self._extract_origin_port(query)
        destination_port = self._extract_destination_port(query)
        
        # Obtener rutas marítimas
        routes_result = self.maritime_partner_tool.run({
            "query_type": "get_maritime_routes",
            "origin_port": origin_port,
            "destination_port": destination_port
        })
        
        return {
            "agent": self.name,
            "query_type": "route_optimization",
            "analysis": f"Optimización de rutas marítimas desde {origin_port} hasta {destination_port}",
            "result": routes_result,
            "confidence": 0.88,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_lay_time_analysis(self, query: str) -> Dict[str, Any]:
        """Maneja consultas de análisis de tiempos de estadía."""
        port_name = self._extract_port_name(query)
        cargo_weight = self._extract_cargo_weight(query)
        
        # Analizar tiempo de estadía
        lay_time_result = self.maritime_partner_tool.run({
            "query_type": "analyze_lay_time",
            "origin_port": port_name,
            "cargo_weight": cargo_weight
        })
        
        return {
            "agent": self.name,
            "query_type": "lay_time_analysis",
            "analysis": f"Análisis de tiempo de estadía en {port_name} para {cargo_weight} toneladas",
            "result": lay_time_result,
            "confidence": 0.93,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_port_availability(self, query: str) -> Dict[str, Any]:
        """Maneja consultas de disponibilidad portuaria."""
        port_name = self._extract_port_name(query)
        
        # Verificar disponibilidad
        availability_result = self.port_coordination_tool.run({
            "query_type": "check_port_availability",
            "port_name": port_name
        })
        
        return {
            "agent": self.name,
            "query_type": "port_availability",
            "analysis": f"Verificación de disponibilidad en {port_name}",
            "result": availability_result,
            "confidence": 0.91,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Maneja consultas generales de logística marítima."""
        return {
            "agent": self.name,
            "query_type": "general",
            "analysis": "Consulta general sobre logística marítima",
            "result": {
                "message": "Soy el especialista en logística marítima. Puedo ayudarte con selección de buques, coordinación portuaria, cálculo de fletes y optimización de rutas.",
                "available_services": [
                    "Selección de buques",
                    "Coordinación portuaria", 
                    "Cálculo de fletes",
                    "Optimización de rutas",
                    "Análisis de tiempos de estadía"
                ]
            },
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_plan_maritime_transport(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la skill de planificación de transporte marítimo."""
        cargo_weight = parameters.get("cargo_weight", 0)
        origin_port = parameters.get("origin_port", "")
        destination_port = parameters.get("destination_port", "")
        
        # Seleccionar buque óptimo
        vessel_result = self.vessel_selection_tool.run({
            "query_type": "select_optimal_vessel",
            "cargo_weight": cargo_weight,
            "origin_port": origin_port,
            "destination_port": destination_port
        })
        
        # Calcular flete
        freight_result = self.maritime_partner_tool.run({
            "query_type": "calculate_freight",
            "origin_port": origin_port,
            "destination_port": destination_port,
            "cargo_weight": cargo_weight
        })
        
        # Coordinar operaciones portuarias
        port_result = self.port_coordination_tool.run({
            "query_type": "schedule_port_operations",
            "port_name": origin_port,
            "cargo_weight": cargo_weight,
            "operation_type": "loading"
        })
        
        return {
            "skill_id": "plan_maritime_transport",
            "cargo_weight": cargo_weight,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "vessel_selection": vessel_result,
            "freight_calculation": freight_result,
            "port_operations": port_result,
            "total_estimated_cost": freight_result.get("result", {}).get("total_freight_cost", 0),
            "estimated_transit_time": vessel_result.get("result", {}).get("optimal_vessel", {}).get("transit_time_days", 0),
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_select_vessel(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la skill de selección de buques."""
        cargo_weight = parameters.get("cargo_weight", 0)
        origin_port = parameters.get("origin_port", "")
        destination_port = parameters.get("destination_port", "")
        priority_criteria = parameters.get("priority_criteria", ["cost", "speed"])
        
        result = self.vessel_selection_tool.run({
            "query_type": "select_optimal_vessel",
            "cargo_weight": cargo_weight,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "priority_criteria": priority_criteria
        })
        
        return {
            "skill_id": "select_vessel",
            "cargo_weight": cargo_weight,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "priority_criteria": priority_criteria,
            "vessel_selection_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_coordinate_port_operations(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la skill de coordinación de operaciones portuarias."""
        port_name = parameters.get("port_name", "")
        vessel_id = parameters.get("vessel_id", "")
        cargo_weight = parameters.get("cargo_weight", 0)
        operation_type = parameters.get("operation_type", "loading")
        
        # Reservar slot de carga
        reservation_result = self.port_coordination_tool.run({
            "query_type": "reserve_loading_slot",
            "port_name": port_name,
            "vessel_id": vessel_id,
            "cargo_weight": cargo_weight,
            "operation_type": operation_type
        })
        
        # Coordinar atraque
        berthing_result = self.port_coordination_tool.run({
            "query_type": "coordinate_berthing",
            "port_name": port_name,
            "vessel_id": vessel_id
        })
        
        return {
            "skill_id": "coordinate_port_operations",
            "port_name": port_name,
            "vessel_id": vessel_id,
            "cargo_weight": cargo_weight,
            "operation_type": operation_type,
            "reservation": reservation_result,
            "berthing": berthing_result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_calculate_maritime_costs(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la skill de cálculo de costos marítimos."""
        cargo_weight = parameters.get("cargo_weight", 0)
        origin_port = parameters.get("origin_port", "")
        destination_port = parameters.get("destination_port", "")
        vessel_id = parameters.get("vessel_id", "")
        
        # Calcular flete
        freight_result = self.maritime_partner_tool.run({
            "query_type": "calculate_freight",
            "origin_port": origin_port,
            "destination_port": destination_port,
            "cargo_weight": cargo_weight
        })
        
        # Calcular costos del buque si se especifica
        vessel_costs = None
        if vessel_id:
            vessel_costs = self.vessel_selection_tool.run({
                "query_type": "calculate_vessel_costs",
                "vessel_id": vessel_id,
                "cargo_weight": cargo_weight
            })
        
        return {
            "skill_id": "calculate_maritime_costs",
            "cargo_weight": cargo_weight,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "vessel_id": vessel_id,
            "freight_costs": freight_result,
            "vessel_costs": vessel_costs,
            "total_estimated_cost": freight_result.get("result", {}).get("total_freight_cost", 0),
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_optimize_maritime_route(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la skill de optimización de rutas marítimas."""
        origin_port = parameters.get("origin_port", "")
        destination_port = parameters.get("destination_port", "")
        cargo_weight = parameters.get("cargo_weight", 0)
        
        # Obtener rutas disponibles
        routes_result = self.maritime_partner_tool.run({
            "query_type": "get_maritime_routes",
            "origin_port": origin_port,
            "destination_port": destination_port
        })
        
        # Seleccionar buque óptimo para la ruta
        vessel_result = self.vessel_selection_tool.run({
            "query_type": "select_optimal_vessel",
            "cargo_weight": cargo_weight,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "priority_criteria": ["cost", "speed"]
        })
        
        return {
            "skill_id": "optimize_maritime_route",
            "origin_port": origin_port,
            "destination_port": destination_port,
            "cargo_weight": cargo_weight,
            "available_routes": routes_result,
            "optimal_vessel": vessel_result,
            "optimization_summary": {
                "best_route": routes_result.get("result", {}).get("available_routes", [{}])[0] if routes_result.get("result", {}).get("available_routes") else {},
                "optimal_vessel": vessel_result.get("result", {}).get("optimal_vessel", {}),
                "estimated_total_time": vessel_result.get("result", {}).get("optimal_vessel", {}).get("transit_time_days", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_cargo_weight(self, query: str) -> int:
        """Extrae el peso de la carga de la consulta."""
        import re
        weight_match = re.search(r'(\d+)\s*(?:toneladas?|tons?)', query.lower())
        return int(weight_match.group(1)) if weight_match else 1000
    
    def _extract_origin_port(self, query: str) -> str:
        """Extrae el puerto de origen de la consulta."""
        query_lower = query.lower()
        if "cartagena" in query_lower:
            return "cartagena"
        elif "barranquilla" in query_lower:
            return "barranquilla"
        elif "buenaventura" in query_lower:
            return "buenaventura"
        else:
            return "cartagena"  # Puerto por defecto
    
    def _extract_destination_port(self, query: str) -> str:
        """Extrae el puerto de destino de la consulta."""
        query_lower = query.lower()
        if "mobile" in query_lower or "alabama" in query_lower:
            return "mobile"
        elif "miami" in query_lower:
            return "miami"
        elif "houston" in query_lower:
            return "houston"
        else:
            return "mobile"  # Puerto por defecto
    
    def _extract_port_name(self, query: str) -> str:
        """Extrae el nombre del puerto de la consulta."""
        query_lower = query.lower()
        if "cartagena" in query_lower:
            return "cartagena"
        elif "barranquilla" in query_lower:
            return "barranquilla"
        elif "mobile" in query_lower:
            return "mobile"
        else:
            return "cartagena"  # Puerto por defecto
