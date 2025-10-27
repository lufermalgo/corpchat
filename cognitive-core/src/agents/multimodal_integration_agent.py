"""
MultimodalIntegrationAgent para el Core Cognitivo.

Este agente implementa la integración multimodal de transporte terrestre y marítimo,
utilizando Google ADK y el protocolo A2A para coordinar operaciones complejas.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from google.generativeai.client import get_default_retrying_gemini_client
from google.generativeai.types import GenerationConfig, Tool as GeminiTool
from google.generativeai.generative_models import GenerativeModel

from src.agents.base_agent import BaseAgent
from src.shared.types import AgentConfig, AgentSkill, AgentCard
from src.shared.exceptions import AgentError
from src.shared.utils import get_logger
from src.tools.base_tool import BaseTool
from src.tools.multimodal.reverse_planning_tool import ReversePlanningTool
from src.tools.multimodal.multimodal_optimizer_tool import MultimodalOptimizerTool


class MultimodalIntegrationAgent(BaseAgent):
    """
    Agente especializado en integración multimodal de transporte.
    
    Este agente coordina y optimiza las operaciones de transporte terrestre
    y marítimo para lograr una cadena de suministro fluida y eficiente.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Inicializa el MultimodalIntegrationAgent.
        
        Args:
            config: Configuración del agente
        """
        # Inicializar herramientas específicas para este agente
        multimodal_tools: List[BaseTool] = [
            ReversePlanningTool(),
            MultimodalOptimizerTool()
        ]
        
        super().__init__(config, tools=multimodal_tools)
        self.logger = get_logger(f"Agent.{self.name}")
        
        # Configuración específica para integración multimodal
        self._integration_config = {
            "max_coordination_time_hours": 72,
            "min_efficiency_threshold": 0.85,
            "cost_optimization_weight": 0.4,
            "time_optimization_weight": 0.3,
            "reliability_weight": 0.3,
            "default_transfer_points": ["cartagena", "barranquilla"],
            "coordination_algorithms": ["genetic_algorithm", "simulated_annealing", "particle_swarm"]
        }
        
        # Base de datos de casos de integración multimodal
        self._integration_cases = {
            "8000_tons_cement_alabama": {
                "scenario": "Transporte de 8000 toneladas de cemento desde plantas de Argos hasta Mobile, Alabama",
                "origin_plants": ["bogota", "medellin", "cali"],
                "destination": "mobile_alabama",
                "cargo_weight": 8000,
                "delivery_deadline": "2024-12-31",
                "constraints": {
                    "terrestrial": {"max_truck_capacity": 35, "daily_dispatch_limit": 1000},
                    "maritime": {"min_vessel_capacity": 5000, "max_vessel_capacity": 15000},
                    "transfer": {"max_transfer_time": 8, "min_efficiency": 0.9}
                },
                "optimization_objectives": ["minimize_cost", "minimize_time", "maximize_reliability"]
            },
            "5000_tons_clinker_cartagena": {
                "scenario": "Transporte de 5000 toneladas de clinker desde planta hasta puerto",
                "origin_plants": ["bogota"],
                "destination": "cartagena",
                "cargo_weight": 5000,
                "delivery_deadline": "2024-11-15",
                "constraints": {
                    "terrestrial": {"max_truck_capacity": 35, "daily_dispatch_limit": 800},
                    "maritime": {"min_vessel_capacity": 3000, "max_vessel_capacity": 8000},
                    "transfer": {"max_transfer_time": 6, "min_efficiency": 0.85}
                },
                "optimization_objectives": ["minimize_cost", "maximize_efficiency"]
            }
        }
        
        self.logger.info(f"MultimodalIntegrationAgent inicializado con {len(multimodal_tools)} herramientas")
    
    async def handle_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja mensajes entrantes para integración multimodal.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Respuesta del agente
        """
        self.logger.info(f"MultimodalIntegrationAgent recibió mensaje: {message}")
        self.logger.debug(f"Contexto actual: {context}")
        
        try:
            # Determinar tipo de consulta
            query_type = self._determine_query_type(message)
            self.logger.info(f"Tipo de consulta detectado: {query_type}")
            
            # Procesar según el tipo de consulta
            if query_type == "multimodal_optimization":
                response = await self._handle_multimodal_optimization(message, context)
            elif query_type == "reverse_planning":
                response = await self._handle_reverse_planning(message, context)
            elif query_type == "integration_analysis":
                response = await self._handle_integration_analysis(message, context)
            elif query_type == "coordination_scheduling":
                response = await self._handle_coordination_scheduling(message, context)
            elif query_type == "case_study":
                response = await self._handle_case_study(message, context)
            else:
                response = await self._handle_general_query(message, context)
            
            # Agregar metadatos de respuesta
            response["agent"] = self.name
            response["query_type"] = query_type
            response["timestamp"] = datetime.now().isoformat()
            
            self.logger.info(f"MultimodalIntegrationAgent generó respuesta exitosa")
            return response
            
        except Exception as e:
            self.logger.error(f"Error manejando mensaje en MultimodalIntegrationAgent: {e}")
            return {
                "error": str(e),
                "agent": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _determine_query_type(self, message: str) -> str:
        """
        Determina el tipo de consulta basado en el mensaje.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tipo de consulta identificado
        """
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["optimizar", "optimización", "multimodal", "integrado"]):
            return "multimodal_optimization"
        elif any(keyword in message_lower for keyword in ["planificación inversa", "reverse planning", "demanda final"]):
            return "reverse_planning"
        elif any(keyword in message_lower for keyword in ["análisis", "analizar", "evaluar", "comparar"]):
            return "integration_analysis"
        elif any(keyword in message_lower for keyword in ["coordinación", "cronograma", "scheduling", "tiempos"]):
            return "coordination_scheduling"
        elif any(keyword in message_lower for keyword in ["caso", "ejemplo", "8000 toneladas", "alabama"]):
            return "case_study"
        else:
            return "general_query"
    
    async def _handle_multimodal_optimization(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja consultas de optimización multimodal.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Respuesta de optimización multimodal
        """
        self.logger.info("Procesando consulta de optimización multimodal")
        
        # Extraer parámetros del mensaje
        params = self._extract_optimization_params(message, context)
        
        # Ejecutar optimización multimodal
        optimization_result = await self._execute_multimodal_optimization(params)
        
        # Generar respuesta usando LLM
        prompt = f"""
        Eres un especialista en integración multimodal de transporte. 
        
        Has recibido una consulta de optimización multimodal con los siguientes parámetros:
        - Plantas de origen: {params.get('origin_plants', [])}
        - Destino: {params.get('destination', '')}
        - Peso de carga: {params.get('cargo_weight', 0)} toneladas
        - Fecha límite: {params.get('delivery_deadline', '')}
        - Objetivos: {params.get('optimization_objectives', [])}
        
        Resultado de la optimización:
        {optimization_result}
        
        Proporciona una respuesta clara y detallada sobre:
        1. La estrategia de optimización recomendada
        2. Los beneficios esperados
        3. Las consideraciones importantes
        4. Las recomendaciones de implementación
        
        Mantén un tono profesional y técnico, pero accesible.
        """
        
        try:
            llm_response = await self._call_llm(prompt)
            
            return {
                "response": llm_response,
                "optimization_result": optimization_result,
                "query_type": "multimodal_optimization"
            }
            
        except Exception as e:
            self.logger.error(f"Error generando respuesta de optimización: {e}")
            return {
                "response": f"Error en optimización multimodal: {e}",
                "optimization_result": optimization_result,
                "query_type": "multimodal_optimization"
            }
    
    async def _handle_reverse_planning(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja consultas de planificación inversa.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Respuesta de planificación inversa
        """
        self.logger.info("Procesando consulta de planificación inversa")
        
        # Extraer parámetros del mensaje
        params = self._extract_reverse_planning_params(message, context)
        
        # Ejecutar planificación inversa
        planning_result = await self._execute_reverse_planning(params)
        
        # Generar respuesta usando LLM
        prompt = f"""
        Eres un especialista en planificación inversa de logística multimodal.
        
        Has recibido una consulta de planificación inversa con los siguientes parámetros:
        - Producto final: {params.get('final_product', '')}
        - Destino final: {params.get('final_destination', '')}
        - Cantidad requerida: {params.get('required_quantity', 0)} toneladas
        - Fecha límite: {params.get('delivery_deadline', '')}
        
        Resultado de la planificación inversa:
        {planning_result}
        
        Proporciona una respuesta detallada sobre:
        1. La estrategia de planificación inversa recomendada
        2. Los puntos de origen identificados
        3. El cronograma de ejecución
        4. Las consideraciones críticas
        
        Mantén un tono profesional y técnico.
        """
        
        try:
            llm_response = await self._call_llm(prompt)
            
            return {
                "response": llm_response,
                "planning_result": planning_result,
                "query_type": "reverse_planning"
            }
            
        except Exception as e:
            self.logger.error(f"Error generando respuesta de planificación inversa: {e}")
            return {
                "response": f"Error en planificación inversa: {e}",
                "planning_result": planning_result,
                "query_type": "reverse_planning"
            }
    
    async def _handle_integration_analysis(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja consultas de análisis de integración.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Respuesta de análisis de integración
        """
        self.logger.info("Procesando consulta de análisis de integración")
        
        # Generar análisis de integración
        analysis_result = await self._generate_integration_analysis(message, context)
        
        # Generar respuesta usando LLM
        prompt = f"""
        Eres un especialista en análisis de integración multimodal.
        
        Has recibido una consulta de análisis con el siguiente contexto:
        {message}
        
        Resultado del análisis:
        {analysis_result}
        
        Proporciona una respuesta detallada sobre:
        1. El estado actual de la integración
        2. Las oportunidades de mejora identificadas
        3. Las recomendaciones estratégicas
        4. El plan de implementación sugerido
        
        Mantén un tono analítico y profesional.
        """
        
        try:
            llm_response = await self._call_llm(prompt)
            
            return {
                "response": llm_response,
                "analysis_result": analysis_result,
                "query_type": "integration_analysis"
            }
            
        except Exception as e:
            self.logger.error(f"Error generando respuesta de análisis: {e}")
            return {
                "response": f"Error en análisis de integración: {e}",
                "analysis_result": analysis_result,
                "query_type": "integration_analysis"
            }
    
    async def _handle_coordination_scheduling(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja consultas de coordinación y programación.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Respuesta de coordinación y programación
        """
        self.logger.info("Procesando consulta de coordinación y programación")
        
        # Generar cronograma de coordinación
        schedule_result = await self._generate_coordination_schedule(message, context)
        
        # Generar respuesta usando LLM
        prompt = f"""
        Eres un especialista en coordinación y programación multimodal.
        
        Has recibido una consulta de coordinación con el siguiente contexto:
        {message}
        
        Resultado del cronograma:
        {schedule_result}
        
        Proporciona una respuesta detallada sobre:
        1. El cronograma de coordinación recomendado
        2. Los puntos críticos de sincronización
        3. Las estrategias de mitigación de riesgos
        4. Las recomendaciones de monitoreo
        
        Mantén un tono operativo y práctico.
        """
        
        try:
            llm_response = await self._call_llm(prompt)
            
            return {
                "response": llm_response,
                "schedule_result": schedule_result,
                "query_type": "coordination_scheduling"
            }
            
        except Exception as e:
            self.logger.error(f"Error generando respuesta de coordinación: {e}")
            return {
                "response": f"Error en coordinación y programación: {e}",
                "schedule_result": schedule_result,
                "query_type": "coordination_scheduling"
            }
    
    async def _handle_case_study(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja consultas de casos de estudio.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Respuesta de caso de estudio
        """
        self.logger.info("Procesando consulta de caso de estudio")
        
        # Identificar caso específico
        case_id = self._identify_case_study(message)
        
        if case_id in self._integration_cases:
            case_data = self._integration_cases[case_id]
            
            # Generar análisis del caso
            case_analysis = await self._analyze_case_study(case_data)
            
            # Generar respuesta usando LLM
            prompt = f"""
            Eres un especialista en casos de estudio de integración multimodal.
            
            Has recibido una consulta sobre el siguiente caso:
            {case_data['scenario']}
            
            Datos del caso:
            - Plantas de origen: {case_data['origin_plants']}
            - Destino: {case_data['destination']}
            - Peso de carga: {case_data['cargo_weight']} toneladas
            - Fecha límite: {case_data['delivery_deadline']}
            - Restricciones: {case_data['constraints']}
            - Objetivos: {case_data['optimization_objectives']}
            
            Análisis del caso:
            {case_analysis}
            
            Proporciona una respuesta detallada sobre:
            1. La estrategia de integración multimodal recomendada
            2. Los desafíos identificados y sus soluciones
            3. Los beneficios esperados
            4. Las lecciones aprendidas
            
            Mantén un tono educativo y profesional.
            """
            
            try:
                llm_response = await self._call_llm(prompt)
                
                return {
                    "response": llm_response,
                    "case_analysis": case_analysis,
                    "case_data": case_data,
                    "query_type": "case_study"
                }
                
            except Exception as e:
                self.logger.error(f"Error generando respuesta de caso de estudio: {e}")
                return {
                    "response": f"Error en análisis de caso de estudio: {e}",
                    "case_analysis": case_analysis,
                    "case_data": case_data,
                    "query_type": "case_study"
                }
        else:
            return {
                "response": "Caso de estudio no encontrado. Casos disponibles: " + ", ".join(self._integration_cases.keys()),
                "query_type": "case_study"
            }
    
    async def _handle_general_query(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja consultas generales.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Respuesta general
        """
        self.logger.info("Procesando consulta general")
        
        # Generar respuesta usando LLM
        prompt = f"""
        Eres un especialista en integración multimodal de transporte para Argos.
        
        Has recibido la siguiente consulta:
        {message}
        
        Contexto de la conversación:
        {context}
        
        Proporciona una respuesta útil y profesional sobre integración multimodal,
        considerando las capacidades y herramientas disponibles.
        
        Mantén un tono profesional y técnico.
        """
        
        try:
            llm_response = await self._call_llm(prompt)
            
            return {
                "response": llm_response,
                "query_type": "general_query"
            }
            
        except Exception as e:
            self.logger.error(f"Error generando respuesta general: {e}")
            return {
                "response": f"Error procesando consulta: {e}",
                "query_type": "general_query"
            }
    
    def _extract_optimization_params(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae parámetros de optimización del mensaje."""
        # Implementación simplificada - en producción se usaría NLP más avanzado
        params = {
            "origin_plants": ["bogota", "medellin", "cali"],
            "destination": "mobile_alabama",
            "cargo_weight": 8000,
            "delivery_deadline": "2024-12-31",
            "optimization_objectives": ["minimize_cost", "minimize_time", "maximize_reliability"]
        }
        
        # Extraer parámetros específicos del mensaje si están presentes
        if "8000" in message:
            params["cargo_weight"] = 8000
        if "alabama" in message.lower():
            params["destination"] = "mobile_alabama"
        if "cartagena" in message.lower():
            params["destination"] = "cartagena"
        
        return params
    
    def _extract_reverse_planning_params(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae parámetros de planificación inversa del mensaje."""
        params = {
            "final_product": "cemento",
            "final_destination": "mobile_alabama",
            "required_quantity": 8000,
            "delivery_deadline": "2024-12-31"
        }
        
        # Extraer parámetros específicos del mensaje
        if "cemento" in message.lower():
            params["final_product"] = "cemento"
        if "clinker" in message.lower():
            params["final_product"] = "clinker"
        if "8000" in message:
            params["required_quantity"] = 8000
        
        return params
    
    def _identify_case_study(self, message: str) -> str:
        """Identifica el caso de estudio específico."""
        message_lower = message.lower()
        
        if "8000" in message and "alabama" in message_lower:
            return "8000_tons_cement_alabama"
        elif "5000" in message and "cartagena" in message_lower:
            return "5000_tons_clinker_cartagena"
        else:
            return "8000_tons_cement_alabama"  # Caso por defecto
    
    async def _execute_multimodal_optimization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta optimización multimodal."""
        try:
            # Usar herramienta de optimización multimodal
            optimization_tool = self.tools["multimodal_optimizer_tool"]
            
            query = {
                "query_type": "optimize_multimodal_route",
                "origin_plants": params.get("origin_plants", []),
                "destination": params.get("destination", ""),
                "cargo_weight": params.get("cargo_weight", 0),
                "delivery_deadline": params.get("delivery_deadline", ""),
                "optimization_objectives": params.get("optimization_objectives", [])
            }
            
            result = await optimization_tool.execute(query)
            return result
            
        except Exception as e:
            self.logger.error(f"Error ejecutando optimización multimodal: {e}")
            return {"error": str(e)}
    
    async def _execute_reverse_planning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta planificación inversa."""
        try:
            # Usar herramienta de planificación inversa
            reverse_planning_tool = self.tools["reverse_planning_tool"]
            
            query = {
                "query_type": "reverse_planning",
                "final_product": params.get("final_product", ""),
                "final_destination": params.get("final_destination", ""),
                "required_quantity": params.get("required_quantity", 0),
                "delivery_deadline": params.get("delivery_deadline", "")
            }
            
            result = await reverse_planning_tool.execute(query)
            return result
            
        except Exception as e:
            self.logger.error(f"Error ejecutando planificación inversa: {e}")
            return {"error": str(e)}
    
    async def _generate_integration_analysis(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera análisis de integración."""
        return {
            "integration_status": "partial",
            "efficiency_score": 0.85,
            "improvement_opportunities": [
                "Mejorar coordinación entre modos",
                "Optimizar puntos de transferencia",
                "Implementar monitoreo en tiempo real"
            ],
            "recommendations": [
                "Implementar sistema de coordinación centralizado",
                "Mejorar infraestructura de transferencia",
                "Desarrollar métricas de rendimiento integradas"
            ]
        }
    
    async def _generate_coordination_schedule(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera cronograma de coordinación."""
        return {
            "coordination_timeline": {
                "terrestrial_departure": "2024-12-15T06:00:00",
                "terrestrial_arrival": "2024-12-17T18:00:00",
                "maritime_departure": "2024-12-18T08:00:00",
                "maritime_arrival": "2024-12-25T12:00:00",
                "final_delivery": "2024-12-26T00:00:00"
            },
            "critical_sync_points": [
                "Transferencia en puerto",
                "Coordinación de tiempos de carga",
                "Sincronización de llegadas"
            ],
            "risk_mitigation": [
                "Buffers de tiempo en transferencias",
                "Planes de contingencia",
                "Monitoreo en tiempo real"
            ]
        }
    
    async def _analyze_case_study(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza un caso de estudio específico."""
        return {
            "case_summary": case_data["scenario"],
            "challenges": [
                "Coordinación entre modos de transporte",
                "Optimización de puntos de transferencia",
                "Gestión de restricciones operativas"
            ],
            "solutions": [
                "Implementar sistema de coordinación multimodal",
                "Optimizar operaciones de transferencia",
                "Desarrollar métricas de rendimiento integradas"
            ],
            "expected_benefits": [
                "Reducción de costos del 15-20%",
                "Mejora de eficiencia del 25%",
                "Aumento de confiabilidad del 30%"
            ],
            "implementation_plan": [
                "Fase 1: Análisis y diseño (4 semanas)",
                "Fase 2: Desarrollo e implementación (8 semanas)",
                "Fase 3: Pruebas y optimización (4 semanas)"
            ]
        }
    
    def get_agent_card(self) -> AgentCard:
        """
        Genera una tarjeta de agente para el protocolo A2A.
        
        Returns:
            AgentCard con información del agente
        """
        return AgentCard(
            id=self.name,
            name=self.name,
            description=self.description,
            skills=[skill.model_dump() for skill in self.skills],
            endpoints={
                "chat": f"/agents/{self.name}/chat",
                "optimize": f"/agents/{self.name}/optimize",
                "plan": f"/agents/{self.name}/plan"
            },
            metadata={
                "model": self.model_name,
                "tools": list(self.tools.keys()),
                "integration_config": self._integration_config,
                "available_cases": list(self._integration_cases.keys())
            }
        )


def create_multimodal_integration_agent(config: AgentConfig) -> MultimodalIntegrationAgent:
    """
    Crea una instancia de MultimodalIntegrationAgent.
    
    Args:
        config: Configuración del agente
        
    Returns:
        Instancia configurada del agente
    """
    return MultimodalIntegrationAgent(config)
