"""
Orchestrator - Orquestador de Agentes.

Coordina la ejecución de múltiples agentes usando diferentes estrategias.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from google.adk.workflows import SequentialAgent, ParallelAgent, LoopAgent

from ..a2a.request_context import RequestContext
from ..a2a.event_queue import EventQueue
from ..shared.types import ProcessedData
from ..shared.exceptions import OrchestrationError
from ..shared.utils import get_logger


class OrchestrationStrategy(Enum):
    """Estrategias de orquestación disponibles."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    LOOP = "loop"
    CONDITIONAL = "conditional"


class OrchestrationStatus(Enum):
    """Estados de orquestación."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Orchestrator:
    """
    Orquestador de agentes del Cognitive Core.
    
    Coordina la ejecución de múltiples agentes usando diferentes estrategias
    basadas en Google ADK workflows.
    """
    
    def __init__(self, config: Any):
        """
        Inicializa el Orchestrator.
        
        Args:
            config: Configuración del core
        """
        self.config = config
        self.logger = get_logger("Orchestrator")
        
        # Estrategias disponibles
        self.strategies = {
            OrchestrationStrategy.SEQUENTIAL: self._sequential_orchestration,
            OrchestrationStrategy.PARALLEL: self._parallel_orchestration,
            OrchestrationStrategy.LOOP: self._loop_orchestration,
            OrchestrationStrategy.CONDITIONAL: self._conditional_orchestration
        }
        
        self.logger.info("Orchestrator inicializado")
    
    async def orchestrate(
        self,
        agents: List[Any],
        processed_input: ProcessedData,
        strategy: str = "sequential"
    ) -> List[Dict[str, Any]]:
        """
        Orquesta la ejecución de agentes.
        
        Args:
            agents: Lista de agentes a ejecutar
            processed_input: Input procesado
            strategy: Estrategia de orquestación
            
        Returns:
            Lista de respuestas de agentes
        """
        try:
            strategy_enum = OrchestrationStrategy(strategy)
            orchestration_func = self.strategies.get(strategy_enum)
            
            if not orchestration_func:
                raise OrchestrationError(f"Estrategia no soportada: {strategy}")
            
            self.logger.info(f"Orquestando {len(agents)} agentes con estrategia: {strategy}")
            
            # Ejecutar orquestación
            responses = await orchestration_func(agents, processed_input)
            
            self.logger.info(f"Orquestación completada: {len(responses)} respuestas")
            return responses
            
        except Exception as e:
            self.logger.error(f"Error en orquestación: {e}")
            raise OrchestrationError(f"Error orquestando agentes: {e}")
    
    async def _sequential_orchestration(
        self,
        agents: List[Any],
        processed_input: ProcessedData
    ) -> List[Dict[str, Any]]:
        """
        Orquestación secuencial de agentes.
        
        Args:
            agents: Lista de agentes
            processed_input: Input procesado
            
        Returns:
            Lista de respuestas
        """
        responses = []
        
        for agent in agents:
            try:
                # Crear contexto de petición
                context = RequestContext(
                    message=processed_input.get("text", ""),
                    request_id=f"seq_{datetime.now().timestamp()}"
                )
                
                # Crear cola de eventos
                event_queue = EventQueue()
                
                # Ejecutar agente
                await agent.execute(context, event_queue)
                
                # Obtener respuesta
                response = await event_queue.get()
                if response:
                    responses.append({
                        "agent": agent.name,
                        "response": response.content,
                        "metadata": response.metadata
                    })
                
            except Exception as e:
                self.logger.error(f"Error ejecutando agente {agent.name}: {e}")
                responses.append({
                    "agent": agent.name,
                    "error": str(e),
                    "status": "failed"
                })
        
        return responses
    
    async def _parallel_orchestration(
        self,
        agents: List[Any],
        processed_input: ProcessedData
    ) -> List[Dict[str, Any]]:
        """
        Orquestación paralela de agentes.
        
        Args:
            agents: Lista de agentes
            processed_input: Input procesado
            
        Returns:
            Lista de respuestas
        """
        # Crear tareas para ejecución paralela
        tasks = []
        
        for agent in agents:
            task = self._execute_agent_async(agent, processed_input)
            tasks.append(task)
        
        # Ejecutar todas las tareas en paralelo
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar respuestas
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                processed_responses.append({
                    "agent": agents[i].name,
                    "error": str(response),
                    "status": "failed"
                })
            else:
                processed_responses.append(response)
        
        return processed_responses
    
    async def _loop_orchestration(
        self,
        agents: List[Any],
        processed_input: ProcessedData
    ) -> List[Dict[str, Any]]:
        """
        Orquestación en bucle de agentes.
        
        Args:
            agents: Lista de agentes
            processed_input: Input procesado
            
        Returns:
            Lista de respuestas
        """
        responses = []
        max_iterations = self.config.orchestration.get("max_iterations", 5)
        
        for iteration in range(max_iterations):
            iteration_responses = []
            
            for agent in agents:
                try:
                    # Crear contexto con información de iteración
                    context = RequestContext(
                        message=processed_input.get("text", ""),
                        request_id=f"loop_{iteration}_{datetime.now().timestamp()}"
                    )
                    context.metadata["iteration"] = iteration
                    
                    # Ejecutar agente
                    event_queue = EventQueue()
                    await agent.execute(context, event_queue)
                    
                    # Obtener respuesta
                    response = await event_queue.get()
                    if response:
                        iteration_responses.append({
                            "agent": agent.name,
                            "iteration": iteration,
                            "response": response.content,
                            "metadata": response.metadata
                        })
                
                except Exception as e:
                    self.logger.error(f"Error en iteración {iteration}, agente {agent.name}: {e}")
                    iteration_responses.append({
                        "agent": agent.name,
                        "iteration": iteration,
                        "error": str(e),
                        "status": "failed"
                    })
            
            responses.extend(iteration_responses)
            
            # Verificar condición de parada
            if self._should_stop_loop(iteration_responses):
                break
        
        return responses
    
    async def _conditional_orchestration(
        self,
        agents: List[Any],
        processed_input: ProcessedData
    ) -> List[Dict[str, Any]]:
        """
        Orquestación condicional de agentes.
        
        Args:
            agents: Lista de agentes
            processed_input: Input procesado
            
        Returns:
            Lista de respuestas
        """
        responses = []
        
        for agent in agents:
            # Evaluar condición para ejecutar agente
            if self._should_execute_agent(agent, processed_input):
                try:
                    context = RequestContext(
                        message=processed_input.get("text", ""),
                        request_id=f"cond_{datetime.now().timestamp()}"
                    )
                    
                    event_queue = EventQueue()
                    await agent.execute(context, event_queue)
                    
                    response = await event_queue.get()
                    if response:
                        responses.append({
                            "agent": agent.name,
                            "response": response.content,
                            "metadata": response.metadata,
                            "condition_met": True
                        })
                
                except Exception as e:
                    self.logger.error(f"Error ejecutando agente {agent.name}: {e}")
                    responses.append({
                        "agent": agent.name,
                        "error": str(e),
                        "status": "failed",
                        "condition_met": True
                    })
            else:
                responses.append({
                    "agent": agent.name,
                    "status": "skipped",
                    "condition_met": False,
                    "reason": "Condition not met"
                })
        
        return responses
    
    async def _execute_agent_async(
        self,
        agent: Any,
        processed_input: ProcessedData
    ) -> Dict[str, Any]:
        """
        Ejecuta un agente de forma asíncrona.
        
        Args:
            agent: Agente a ejecutar
            processed_input: Input procesado
            
        Returns:
            Respuesta del agente
        """
        try:
            context = RequestContext(
                message=processed_input.get("text", ""),
                request_id=f"async_{datetime.now().timestamp()}"
            )
            
            event_queue = EventQueue()
            await agent.execute(context, event_queue)
            
            response = await event_queue.get()
            if response:
                return {
                    "agent": agent.name,
                    "response": response.content,
                    "metadata": response.metadata,
                    "status": "completed"
                }
            else:
                return {
                    "agent": agent.name,
                    "status": "no_response"
                }
        
        except Exception as e:
            return {
                "agent": agent.name,
                "error": str(e),
                "status": "failed"
            }
    
    def _should_stop_loop(self, responses: List[Dict[str, Any]]) -> bool:
        """
        Determina si debe parar el bucle.
        
        Args:
            responses: Respuestas de la iteración
            
        Returns:
            True si debe parar
        """
        # Lógica simple: parar si hay errores
        for response in responses:
            if response.get("status") == "failed":
                return True
        
        return False
    
    def _should_execute_agent(self, agent: Any, processed_input: ProcessedData) -> bool:
        """
        Determina si debe ejecutar un agente.
        
        Args:
            agent: Agente a evaluar
            processed_input: Input procesado
            
        Returns:
            True si debe ejecutar
        """
        # Lógica simple: ejecutar todos los agentes
        return True
    
    def get_available_strategies(self) -> List[str]:
        """
        Retorna las estrategias disponibles.
        
        Returns:
            Lista de estrategias
        """
        return [strategy.value for strategy in OrchestrationStrategy]


def create_orchestrator(config: Any) -> Orchestrator:
    """
    Crea una instancia del Orchestrator.
    
    Args:
        config: Configuración del core
        
    Returns:
        Instancia del Orchestrator
    """
    return Orchestrator(config)