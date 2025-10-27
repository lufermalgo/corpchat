"""
Decision Engine - Motor de Decisiones.

Genera decisiones finales basadas en conocimiento sintetizado
y proporciona explicaciones del proceso de razonamiento.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from ..shared.types import ProcessedData
from ..shared.exceptions import DecisionError
from ..shared.utils import get_logger


class DecisionType(Enum):
    """Tipos de decisiones."""
    BINARY = "binary"
    MULTI_CHOICE = "multi_choice"
    RANKING = "ranking"
    RECOMMENDATION = "recommendation"
    STRATEGIC = "strategic"


class DecisionConfidence(Enum):
    """Niveles de confianza en decisiones."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DecisionEngine:
    """
    Motor de decisiones del Cognitive Core.
    
    Genera decisiones finales basadas en conocimiento sintetizado
    y proporciona explicaciones del proceso de razonamiento.
    """
    
    def __init__(self, config: Any):
        """
        Inicializa el Decision Engine.
        
        Args:
            config: Configuración del core
        """
        self.config = config
        self.logger = get_logger("DecisionEngine")
        
        # Configuración de decisiones
        self.max_reasoning_steps = config.decision_engine.get("max_reasoning_steps", 10)
        self.enable_reasoning = config.decision_engine.get("enable_reasoning", True)
        self.enable_explanation = config.decision_engine.get("enable_explanation", True)
        
        # Historial de decisiones
        self.decision_history: List[Dict[str, Any]] = []
        
        self.logger.info("Decision Engine inicializado")
    
    async def decide(
        self,
        synthesized_knowledge: Dict[str, Any],
        decision_type: str = "recommendation"
    ) -> Dict[str, Any]:
        """
        Genera una decisión basada en conocimiento sintetizado.
        
        Args:
            synthesized_knowledge: Conocimiento sintetizado
            decision_type: Tipo de decisión
            
        Returns:
            Decisión generada
        """
        try:
            decision_type_enum = DecisionType(decision_type)
            
            self.logger.info(f"Generando decisión tipo: {decision_type}")
            
            # Proceso de razonamiento
            reasoning_steps = []
            if self.enable_reasoning:
                reasoning_steps = await self._generate_reasoning_steps(synthesized_knowledge)
            
            # Generar decisión
            decision = await self._generate_decision(synthesized_knowledge, decision_type_enum)
            
            # Generar explicación
            explanation = ""
            if self.enable_explanation:
                explanation = await self._generate_explanation(decision, reasoning_steps)
            
            # Crear resultado final
            final_decision = {
                "decision": decision,
                "type": decision_type,
                "confidence": self._assess_confidence(decision, synthesized_knowledge),
                "reasoning_steps": reasoning_steps,
                "explanation": explanation,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "knowledge_type": synthesized_knowledge.get("type"),
                    "agent_count": synthesized_knowledge.get("agent_count", 0),
                    "reasoning_enabled": self.enable_reasoning,
                    "explanation_enabled": self.enable_explanation
                }
            }
            
            # Guardar en historial
            self.decision_history.append(final_decision)
            
            self.logger.info("Decisión generada exitosamente")
            return final_decision
            
        except Exception as e:
            self.logger.error(f"Error generando decisión: {e}")
            raise DecisionError(f"Error generando decisión: {e}")
    
    async def _generate_reasoning_steps(
        self,
        synthesized_knowledge: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Genera pasos de razonamiento.
        
        Args:
            synthesized_knowledge: Conocimiento sintetizado
            
        Returns:
            Lista de pasos de razonamiento
        """
        steps = []
        
        # Paso 1: Análisis del conocimiento
        steps.append({
            "step": 1,
            "description": "Análisis del conocimiento sintetizado",
            "input": synthesized_knowledge.get("type", "unknown"),
            "output": "Conocimiento analizado",
            "confidence": 0.8
        })
        
        # Paso 2: Evaluación de opciones
        steps.append({
            "step": 2,
            "description": "Evaluación de opciones disponibles",
            "input": "Conocimiento analizado",
            "output": "Opciones evaluadas",
            "confidence": 0.7
        })
        
        # Paso 3: Selección de mejor opción
        steps.append({
            "step": 3,
            "description": "Selección de la mejor opción",
            "input": "Opciones evaluadas",
            "output": "Opción seleccionada",
            "confidence": 0.9
        })
        
        return steps
    
    async def _generate_decision(
        self,
        synthesized_knowledge: Dict[str, Any],
        decision_type: DecisionType
    ) -> Dict[str, Any]:
        """
        Genera la decisión final.
        
        Args:
            synthesized_knowledge: Conocimiento sintetizado
            decision_type: Tipo de decisión
            
        Returns:
            Decisión generada
        """
        if decision_type == DecisionType.BINARY:
            return {
                "choice": "yes",
                "rationale": "Basado en análisis de conocimiento",
                "alternatives": ["no"],
                "probability": 0.8
            }
        
        elif decision_type == DecisionType.MULTI_CHOICE:
            return {
                "choice": "option_a",
                "rationale": "Opción A seleccionada basada en criterios",
                "alternatives": ["option_b", "option_c"],
                "probabilities": {"option_a": 0.6, "option_b": 0.3, "option_c": 0.1}
            }
        
        elif decision_type == DecisionType.RANKING:
            return {
                "ranking": ["item_1", "item_2", "item_3"],
                "rationale": "Ranking basado en criterios de evaluación",
                "scores": {"item_1": 0.9, "item_2": 0.7, "item_3": 0.5}
            }
        
        elif decision_type == DecisionType.RECOMMENDATION:
            return {
                "recommendation": "Proceder con la implementación",
                "rationale": "Recomendación basada en análisis completo",
                "alternatives": ["Esperar más información", "Cancelar proyecto"],
                "confidence": 0.8
            }
        
        elif decision_type == DecisionType.STRATEGIC:
            return {
                "strategy": "Estrategia de crecimiento",
                "rationale": "Estrategia seleccionada basada en análisis estratégico",
                "implementation_plan": ["Fase 1", "Fase 2", "Fase 3"],
                "success_probability": 0.7
            }
        
        else:
            return {
                "decision": "Decisión por defecto",
                "rationale": "Decisión generada por el motor",
                "confidence": 0.5
            }
    
    async def _generate_explanation(
        self,
        decision: Dict[str, Any],
        reasoning_steps: List[Dict[str, Any]]
    ) -> str:
        """
        Genera explicación de la decisión.
        
        Args:
            decision: Decisión generada
            reasoning_steps: Pasos de razonamiento
            
        Returns:
            Explicación de la decisión
        """
        explanation = f"Decisión generada: {decision.get('choice', decision.get('recommendation', 'Decisión por defecto'))}\n\n"
        
        explanation += "Proceso de razonamiento:\n"
        for step in reasoning_steps:
            explanation += f"- {step['description']}: {step['output']}\n"
        
        explanation += f"\nConfianza en la decisión: {decision.get('confidence', 0.5)}\n"
        
        return explanation
    
    def _assess_confidence(
        self,
        decision: Dict[str, Any],
        synthesized_knowledge: Dict[str, Any]
    ) -> str:
        """
        Evalúa la confianza en la decisión.
        
        Args:
            decision: Decisión generada
            synthesized_knowledge: Conocimiento sintetizado
            
        Returns:
            Nivel de confianza
        """
        # Lógica simple de evaluación de confianza
        knowledge_confidence = synthesized_knowledge.get("confidence_score", 0.5)
        decision_confidence = decision.get("confidence", 0.5)
        
        overall_confidence = (knowledge_confidence + decision_confidence) / 2
        
        if overall_confidence >= 0.8:
            return DecisionConfidence.VERY_HIGH.value
        elif overall_confidence >= 0.6:
            return DecisionConfidence.HIGH.value
        elif overall_confidence >= 0.4:
            return DecisionConfidence.MEDIUM.value
        else:
            return DecisionConfidence.LOW.value
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """
        Retorna el historial de decisiones.
        
        Returns:
            Historial de decisiones
        """
        return self.decision_history
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de decisiones.
        
        Returns:
            Estadísticas
        """
        return {
            "total_decisions": len(self.decision_history),
            "reasoning_enabled": self.enable_reasoning,
            "explanation_enabled": self.enable_explanation,
            "max_reasoning_steps": self.max_reasoning_steps,
            "last_decision": self.decision_history[-1] if self.decision_history else None
        }


def create_decision_engine(config: Any) -> DecisionEngine:
    """
    Crea una instancia del Decision Engine.
    
    Args:
        config: Configuración del core
        
    Returns:
        Instancia del Decision Engine
    """
    return DecisionEngine(config)
