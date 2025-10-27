"""
TerrestrialLogisticsAgent para el Core Cognitivo.

Este agente especializado maneja toda la logística terrestre de Argos,
incluyendo optimización de flota GPS, rutas y monitoreo de geocercas.
Implementa LlmAgent de Google ADK con herramientas especializadas.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..agents.base_agent import BaseAgent
from ..shared.types import AgentConfig, AgentSkill, ToolConfig, AgentType
from ..shared.exceptions import AgentError, ToolError
from ..shared.utils import get_logger, measure_time
from ..tools.terrestrial.gps_fleet_tool import create_gps_fleet_tool
from ..tools.terrestrial.route_optimizer_tool import create_route_optimizer_tool
from ..tools.terrestrial.geofence_tool import create_geofence_tool


class TerrestrialLogisticsAgent(BaseAgent):
    """
    Agente especializado en logística terrestre de Argos.
    
    Maneja transporte terrestre desde plantas hasta puertos usando
    flota GPS, optimización de rutas y monitoreo de geocercas.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Inicializa el TerrestrialLogisticsAgent.
        
        Args:
            config: Configuración del agente
            
        Raises:
            AgentError: Si hay error inicializando el agente
        """
        super().__init__(config)
        
        self._logger = get_logger(__name__)
        self._tools_instances = self._initialize_tools()
        self._logger.info(f"TerrestrialLogisticsAgent {self.name} inicializado")
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """
        Inicializa las herramientas del agente.
        
        Returns:
            Diccionario con instancias de herramientas
        """
        try:
            tools = {}
            
            # GPS Fleet Tool
            tools["gps_fleet"] = create_gps_fleet_tool()
            
            # Route Optimizer Tool
            tools["route_optimizer"] = create_route_optimizer_tool()
            
            # Geofence Tool
            tools["geofence"] = create_geofence_tool()
            
            self._logger.info(f"Herramientas inicializadas para {self.name}: {list(tools.keys())}")
            return tools
            
        except Exception as e:
            raise AgentError(f"Error inicializando herramientas de {self.name}: {e}")
    
    @measure_time
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa consulta del usuario relacionada con logística terrestre.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta del agente
            
        Raises:
            AgentError: Si hay error procesando la consulta
        """
        try:
            self._logger.info(f"Procesando consulta terrestre: {query[:100]}...")
            
            # Analizar tipo de consulta
            query_type = self._analyze_query_type(query)
            
            # Procesar según tipo
            if query_type == "fleet_status":
                return self._handle_fleet_status_query(query, context)
            elif query_type == "route_optimization":
                return self._handle_route_optimization_query(query, context)
            elif query_type == "geofence_monitoring":
                return self._handle_geofence_monitoring_query(query, context)
            elif query_type == "transport_planning":
                return self._handle_transport_planning_query(query, context)
            else:
                return self._handle_general_query(query, context)
                
        except Exception as e:
            raise AgentError(f"Error procesando consulta en {self.name}: {e}")
    
    def execute_skill(self, skill_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta un skill específico del agente.
        
        Args:
            skill_id: ID del skill a ejecutar
            input_data: Datos de entrada
            
        Returns:
            Resultado de la ejecución del skill
            
        Raises:
            AgentError: Si hay error ejecutando el skill
        """
        try:
            self._logger.info(f"Ejecutando skill {skill_id} en {self.name}")
            
            if skill_id == "plan_terrestrial_transport":
                return self._execute_plan_terrestrial_transport(input_data)
            elif skill_id == "gps_fleet_optimization":
                return self._execute_gps_fleet_optimization(input_data)
            else:
                raise AgentError(f"Skill no soportado: {skill_id}")
                
        except Exception as e:
            raise AgentError(f"Error ejecutando skill {skill_id} en {self.name}: {e}")
    
    def _analyze_query_type(self, query: str) -> str:
        """
        Analiza el tipo de consulta basado en palabras clave.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Tipo de consulta identificado
        """
        query_lower = query.lower()
        
        # Palabras clave para diferentes tipos de consulta
        fleet_keywords = ["flota", "gps", "camiones", "vehículos", "disponibles", "estado"]
        route_keywords = ["ruta", "optimizar", "distancia", "tiempo", "costo", "mejor"]
        geofence_keywords = ["geocerca", "alerta", "ubicación", "monitoreo", "zona"]
        planning_keywords = ["planificar", "transporte", "enviar", "carga", "toneladas"]
        
        if any(keyword in query_lower for keyword in fleet_keywords):
            return "fleet_status"
        elif any(keyword in query_lower for keyword in route_keywords):
            return "route_optimization"
        elif any(keyword in query_lower for keyword in geofence_keywords):
            return "geofence_monitoring"
        elif any(keyword in query_lower for keyword in planning_keywords):
            return "transport_planning"
        else:
            return "general"
    
    def _handle_fleet_status_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Maneja consultas sobre estado de la flota.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta sobre estado de flota
        """
        try:
            # Extraer parámetros de la consulta
            location_filter = self._extract_location_from_query(query)
            
            # Consultar estado de flota
            fleet_status = self._tools_instances["gps_fleet"].run({
                "query_type": "get_fleet_status",
                "location": location_filter
            })
            
            # Generar respuesta estructurada
            response = {
                "agent": self.name,
                "query_type": "fleet_status",
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "fleet_summary": fleet_status["fleet_summary"],
                    "location_filter": location_filter,
                    "recommendations": self._generate_fleet_recommendations(fleet_status)
                },
                "confidence": 95,
                "tools_used": ["gps_fleet_tool"]
            }
            
            return response
            
        except Exception as e:
            raise AgentError(f"Error manejando consulta de estado de flota: {e}")
    
    def _handle_route_optimization_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Maneja consultas sobre optimización de rutas.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta sobre optimización de rutas
        """
        try:
            # Extraer parámetros de la consulta
            origin, destination, cargo_weight = self._extract_route_parameters(query)
            
            if not origin or not destination:
                raise AgentError("No se pudo identificar origen y destino en la consulta")
            
            # Optimizar ruta
            route_optimization = self._tools_instances["route_optimizer"].run({
                "query_type": "optimize_route",
                "origin": origin,
                "destination": destination,
                "cargo_weight": cargo_weight,
                "priority": "efficiency"
            })
            
            # Generar respuesta estructurada
            response = {
                "agent": self.name,
                "query_type": "route_optimization",
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "optimal_route": route_optimization["optimal_route"],
                    "all_options": route_optimization["all_options"],
                    "recommendation": route_optimization["recommendation"]
                },
                "confidence": 92,
                "tools_used": ["route_optimizer_tool"]
            }
            
            return response
            
        except Exception as e:
            raise AgentError(f"Error manejando consulta de optimización de rutas: {e}")
    
    def _handle_geofence_monitoring_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Maneja consultas sobre monitoreo de geocercas.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta sobre monitoreo de geocercas
        """
        try:
            # Obtener estado de geocercas
            geofence_status = self._tools_instances["geofence"].run({
                "query_type": "get_geofence_status"
            })
            
            # Obtener alertas activas
            active_alerts = self._tools_instances["geofence"].run({
                "query_type": "get_active_alerts",
                "status": "active"
            })
            
            # Generar respuesta estructurada
            response = {
                "agent": self.name,
                "query_type": "geofence_monitoring",
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "geofence_summary": geofence_status["summary"],
                    "active_alerts": active_alerts["alerts"],
                    "alert_statistics": active_alerts["statistics"]
                },
                "confidence": 90,
                "tools_used": ["geofence_tool"]
            }
            
            return response
            
        except Exception as e:
            raise AgentError(f"Error manejando consulta de monitoreo de geocercas: {e}")
    
    def _handle_transport_planning_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Maneja consultas sobre planificación de transporte.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta sobre planificación de transporte
        """
        try:
            # Extraer parámetros de la consulta
            cargo_weight, destination = self._extract_transport_parameters(query)
            
            if cargo_weight <= 0:
                raise AgentError("No se pudo identificar el peso de la carga")
            
            # Obtener vehículos disponibles
            available_vehicles = self._tools_instances["gps_fleet"].run({
                "query_type": "get_available_vehicles",
                "required_capacity": cargo_weight,
                "max_results": 20
            })
            
            # Optimizar asignación de flota
            fleet_optimization = self._tools_instances["gps_fleet"].run({
                "query_type": "optimize_fleet_assignment",
                "cargo_weight": cargo_weight,
                "destination_location": destination
            })
            
            # Generar respuesta estructurada
            response = {
                "agent": self.name,
                "query_type": "transport_planning",
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "cargo_weight": cargo_weight,
                    "available_vehicles": available_vehicles["available_count"],
                    "fleet_assignment": fleet_optimization["assignment"],
                    "efficiency_score": fleet_optimization["efficiency_score"],
                    "recommendations": self._generate_transport_recommendations(fleet_optimization)
                },
                "confidence": 94,
                "tools_used": ["gps_fleet_tool"]
            }
            
            return response
            
        except Exception as e:
            raise AgentError(f"Error manejando consulta de planificación de transporte: {e}")
    
    def _handle_general_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Maneja consultas generales sobre logística terrestre.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta general
        """
        try:
            # Obtener estado general de la flota
            fleet_status = self._tools_instances["gps_fleet"].run({
                "query_type": "get_fleet_status"
            })
            
            # Generar respuesta general
            response = {
                "agent": self.name,
                "query_type": "general",
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "fleet_summary": fleet_status["fleet_summary"],
                    "capabilities": [
                        "Optimización de flota GPS",
                        "Planificación de rutas terrestres",
                        "Monitoreo de geocercas",
                        "Asignación de vehículos"
                    ],
                    "current_status": "Operativo"
                },
                "confidence": 85,
                "tools_used": ["gps_fleet_tool"]
            }
            
            return response
            
        except Exception as e:
            raise AgentError(f"Error manejando consulta general: {e}")
    
    def _execute_plan_terrestrial_transport(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta skill de planificación de transporte terrestre.
        
        Args:
            input_data: Datos de entrada del skill
            
        Returns:
            Resultado de la planificación
        """
        try:
            destination = input_data.get("destination", "Puerto Cartagena")
            cargo_weight = input_data.get("cargo_weight", 0)
            cargo_type = input_data.get("cargo_type", "cement")
            
            # Optimizar asignación de flota
            fleet_optimization = self._tools_instances["gps_fleet"].run({
                "query_type": "optimize_fleet_assignment",
                "cargo_weight": cargo_weight,
                "destination_location": destination
            })
            
            # Calcular rutas óptimas para cada vehículo asignado
            route_analysis = []
            for assignment in fleet_optimization["assignment"]:
                vehicle_location = assignment["current_location"]["name"]
                
                route_opt = self._tools_instances["route_optimizer"].run({
                    "query_type": "optimize_route",
                    "origin": vehicle_location.lower().replace(" ", "_"),
                    "destination": destination.lower().replace(" ", "_"),
                    "cargo_weight": assignment["assigned_weight"]
                })
                
                route_analysis.append({
                    "vehicle_id": assignment["vehicle_id"],
                    "route": route_opt["optimal_route"],
                    "assigned_weight": assignment["assigned_weight"]
                })
            
            return {
                "skill_id": "plan_terrestrial_transport",
                "timestamp": datetime.now().isoformat(),
                "destination": destination,
                "cargo_weight": cargo_weight,
                "cargo_type": cargo_type,
                "trucks_needed": fleet_optimization["trucks_needed"],
                "total_assigned_capacity": fleet_optimization["total_assigned_capacity"],
                "efficiency_score": fleet_optimization["efficiency_score"],
                "route_analysis": route_analysis,
                "estimated_total_cost": sum(r["route"]["estimated_cost_usd"] for r in route_analysis),
                "estimated_total_time": max(r["route"]["estimated_time_hours"] for r in route_analysis)
            }
            
        except Exception as e:
            raise AgentError(f"Error ejecutando skill plan_terrestrial_transport: {e}")
    
    def _execute_gps_fleet_optimization(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta skill de optimización de flota GPS.
        
        Args:
            input_data: Datos de entrada del skill
            
        Returns:
            Resultado de la optimización
        """
        try:
            fleet_size = input_data.get("fleet_size", 150)
            current_locations = input_data.get("current_locations", [])
            
            # Obtener estado actual de la flota
            fleet_status = self._tools_instances["gps_fleet"].run({
                "query_type": "get_fleet_status"
            })
            
            # Optimizar asignación
            optimization_result = self._tools_instances["gps_fleet"].run({
                "query_type": "optimize_fleet_assignment",
                "cargo_weight": 1000,  # Peso de referencia para optimización
                "destination_location": "Puerto Cartagena"
            })
            
            return {
                "skill_id": "gps_fleet_optimization",
                "timestamp": datetime.now().isoformat(),
                "fleet_size": fleet_size,
                "current_locations": current_locations,
                "optimized_assignment": optimization_result["assignment"],
                "efficiency_score": optimization_result["efficiency_score"],
                "recommendations": self._generate_fleet_optimization_recommendations(optimization_result)
            }
            
        except Exception as e:
            raise AgentError(f"Error ejecutando skill gps_fleet_optimization: {e}")
    
    def _extract_location_from_query(self, query: str) -> Optional[str]:
        """Extrae ubicación de la consulta."""
        locations = ["bogotá", "medellín", "cali", "cartagena"]
        query_lower = query.lower()
        
        for location in locations:
            if location in query_lower:
                return location.title()
        return None
    
    def _extract_route_parameters(self, query: str) -> tuple:
        """Extrae parámetros de ruta de la consulta."""
        # Implementación simplificada - en producción usaría NLP más sofisticado
        query_lower = query.lower()
        
        origin = None
        destination = None
        cargo_weight = 0
        
        # Detectar origen y destino
        if "bogotá" in query_lower or "bogota" in query_lower:
            origin = "bogota"
        elif "medellín" in query_lower or "medellin" in query_lower:
            origin = "medellin"
        elif "cali" in query_lower:
            origin = "cali"
        
        if "cartagena" in query_lower:
            destination = "cartagena"
        
        # Detectar peso de carga
        import re
        weight_match = re.search(r'(\d+)\s*toneladas?', query_lower)
        if weight_match:
            cargo_weight = int(weight_match.group(1))
        
        return origin, destination, cargo_weight
    
    def _extract_transport_parameters(self, query: str) -> tuple:
        """Extrae parámetros de transporte de la consulta."""
        query_lower = query.lower()
        
        cargo_weight = 0
        destination = "Puerto Cartagena"  # Default
        
        # Detectar peso
        import re
        weight_match = re.search(r'(\d+)\s*toneladas?', query_lower)
        if weight_match:
            cargo_weight = int(weight_match.group(1))
        
        # Detectar destino
        if "alabama" in query_lower:
            destination = "Alabama, USA"
        elif "cartagena" in query_lower:
            destination = "Puerto Cartagena"
        
        return cargo_weight, destination
    
    def _generate_fleet_recommendations(self, fleet_status: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en estado de flota."""
        recommendations = []
        summary = fleet_status["fleet_summary"]
        
        if summary["utilization_rate"] > 80:
            recommendations.append("Alta utilización de flota - considerar expansión")
        
        if summary["maintenance"] > 10:
            recommendations.append("Múltiples vehículos en mantenimiento - revisar programa")
        
        if summary["available"] < 20:
            recommendations.append("Pocos vehículos disponibles - planificar asignaciones")
        
        return recommendations
    
    def _generate_transport_recommendations(self, optimization: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en optimización de transporte."""
        recommendations = []
        
        if optimization["efficiency_score"] > 90:
            recommendations.append("Excelente optimización de flota")
        elif optimization["efficiency_score"] > 80:
            recommendations.append("Buena optimización de flota")
        else:
            recommendations.append("Considerar ajustes en asignación de flota")
        
        if optimization["remaining_weight"] > 0:
            recommendations.append(f"Peso restante: {optimization['remaining_weight']} toneladas")
        
        return recommendations
    
    def _generate_fleet_optimization_recommendations(self, optimization: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones para optimización de flota."""
        recommendations = []
        
        if optimization["efficiency_score"] > 85:
            recommendations.append("Flota optimizada eficientemente")
        else:
            recommendations.append("Oportunidades de mejora en optimización")
        
        recommendations.append(f"Score de eficiencia: {optimization['efficiency_score']}%")
        
        return recommendations
