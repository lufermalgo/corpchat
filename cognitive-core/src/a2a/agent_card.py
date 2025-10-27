"""
Implementación de Agent Card según especificación A2A Protocol.

Este módulo implementa la funcionalidad de Agent Card para el descubrimiento
y metadata de agentes según el protocolo A2A oficial.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..shared.types import AgentCard, AgentSkill, AuthenticationConfig, AuthenticationType
from ..shared.exceptions import A2AProtocolError, ValidationError
from ..shared.utils import get_logger, get_timestamp, safe_json_dumps
from ..agents.base_agent import BaseAgent


class AgentCardManager:
    """
    Gestor de Agent Cards para el protocolo A2A.
    
    Maneja la creación, validación y gestión de Agent Cards
    según la especificación oficial del protocolo A2A.
    """
    
    def __init__(self):
        """Inicializa el gestor de Agent Cards."""
        self._logger = get_logger(__name__)
        self._agent_cards: Dict[str, AgentCard] = {}
        self._logger.info("AgentCardManager inicializado")
    
    def create_agent_card(self, agent: BaseAgent, endpoint: Optional[str] = None) -> AgentCard:
        """
        Crea un Agent Card a partir de un agente.
        
        Args:
            agent: Instancia del agente
            endpoint: Endpoint del agente (opcional)
            
        Returns:
            Agent Card creado
            
        Raises:
            A2AProtocolError: Si hay error creando el Agent Card
        """
        try:
            # Crear skills del agente
            skills = []
            for skill in agent.skills:
                skills.append(skill)
            
            # Crear configuración de autenticación por defecto
            auth_config = AuthenticationConfig(
                type=AuthenticationType.NONE,
                authorization_endpoint=None,
                token_endpoint=None,
                scopes=None
            )
            
            # Crear Agent Card
            agent_card = AgentCard(
                name=agent.name,
                version="1.0.0",
                description=f"Agent Card para {agent.name}",
                skills=skills,
                authentication=auth_config,
                endpoint=endpoint
            )
            
            # Validar Agent Card
            self._validate_agent_card(agent_card)
            
            # Almacenar Agent Card
            self._agent_cards[agent.name] = agent_card
            
            self._logger.info(f"Agent Card creado para agente {agent.name}")
            return agent_card
            
        except Exception as e:
            raise A2AProtocolError(f"Error creando Agent Card para agente {agent.name}: {e}")
    
    def create_agent_card_with_auth(self, 
                                   agent: BaseAgent, 
                                   auth_type: AuthenticationType,
                                   endpoint: Optional[str] = None,
                                   auth_endpoints: Optional[Dict[str, str]] = None,
                                   scopes: Optional[List[str]] = None) -> AgentCard:
        """
        Crea un Agent Card con configuración de autenticación específica.
        
        Args:
            agent: Instancia del agente
            auth_type: Tipo de autenticación
            endpoint: Endpoint del agente
            auth_endpoints: Endpoints de autenticación
            scopes: Scopes OAuth
            
        Returns:
            Agent Card creado
            
        Raises:
            A2AProtocolError: Si hay error creando el Agent Card
        """
        try:
            # Crear skills del agente
            skills = []
            for skill in agent.skills:
                skills.append(skill)
            
            # Crear configuración de autenticación
            auth_config = AuthenticationConfig(
                type=auth_type,
                authorization_endpoint=auth_endpoints.get("authorization") if auth_endpoints else None,
                token_endpoint=auth_endpoints.get("token") if auth_endpoints else None,
                scopes=scopes
            )
            
            # Crear Agent Card
            agent_card = AgentCard(
                name=agent.name,
                version="1.0.0",
                description=f"Agent Card para {agent.name} con autenticación {auth_type.value}",
                skills=skills,
                authentication=auth_config,
                endpoint=endpoint
            )
            
            # Validar Agent Card
            self._validate_agent_card(agent_card)
            
            # Almacenar Agent Card
            self._agent_cards[agent.name] = agent_card
            
            self._logger.info(f"Agent Card con autenticación creado para agente {agent.name}")
            return agent_card
            
        except Exception as e:
            raise A2AProtocolError(f"Error creando Agent Card con autenticación para agente {agent.name}: {e}")
    
    def get_agent_card(self, agent_name: str) -> Optional[AgentCard]:
        """
        Obtiene Agent Card por nombre de agente.
        
        Args:
            agent_name: Nombre del agente
            
        Returns:
            Agent Card encontrado o None
        """
        return self._agent_cards.get(agent_name)
    
    def get_all_agent_cards(self) -> Dict[str, AgentCard]:
        """
        Obtiene todos los Agent Cards.
        
        Returns:
            Diccionario con todos los Agent Cards
        """
        return self._agent_cards.copy()
    
    def update_agent_card(self, agent_name: str, updates: Dict[str, Any]) -> AgentCard:
        """
        Actualiza un Agent Card existente.
        
        Args:
            agent_name: Nombre del agente
            updates: Actualizaciones a aplicar
            
        Returns:
            Agent Card actualizado
            
        Raises:
            A2AProtocolError: Si el agente no existe o hay error actualizando
        """
        try:
            if agent_name not in self._agent_cards:
                raise A2AProtocolError(f"Agent Card no encontrado para agente {agent_name}")
            
            # Obtener Agent Card existente
            existing_card = self._agent_cards[agent_name]
            
            # Crear nuevo Agent Card con actualizaciones
            updated_data = existing_card.dict()
            updated_data.update(updates)
            
            updated_card = AgentCard(**updated_data)
            
            # Validar Agent Card actualizado
            self._validate_agent_card(updated_card)
            
            # Actualizar almacenamiento
            self._agent_cards[agent_name] = updated_card
            
            self._logger.info(f"Agent Card actualizado para agente {agent_name}")
            return updated_card
            
        except Exception as e:
            raise A2AProtocolError(f"Error actualizando Agent Card para agente {agent_name}: {e}")
    
    def remove_agent_card(self, agent_name: str) -> bool:
        """
        Elimina un Agent Card.
        
        Args:
            agent_name: Nombre del agente
            
        Returns:
            True si se eliminó exitosamente
        """
        if agent_name in self._agent_cards:
            del self._agent_cards[agent_name]
            self._logger.info(f"Agent Card eliminado para agente {agent_name}")
            return True
        return False
    
    def _validate_agent_card(self, agent_card: AgentCard) -> None:
        """
        Valida un Agent Card según especificación A2A.
        
        Args:
            agent_card: Agent Card a validar
            
        Raises:
            ValidationError: Si el Agent Card es inválido
        """
        try:
            # Validar campos requeridos
            if not agent_card.name:
                raise ValidationError("Agent Card sin nombre")
            
            if not agent_card.version:
                raise ValidationError(f"Agent Card {agent_card.name} sin versión")
            
            if not agent_card.description:
                raise ValidationError(f"Agent Card {agent_card.name} sin descripción")
            
            # Validar skills
            if not agent_card.skills:
                raise ValidationError(f"Agent Card {agent_card.name} sin skills")
            
            for skill in agent_card.skills:
                if not skill.id:
                    raise ValidationError(f"Skill sin ID en Agent Card {agent_card.name}")
                if not skill.name:
                    raise ValidationError(f"Skill {skill.id} sin nombre en Agent Card {agent_card.name}")
                if not skill.description:
                    raise ValidationError(f"Skill {skill.id} sin descripción en Agent Card {agent_card.name}")
            
            # Validar autenticación si está presente
            if agent_card.authentication:
                auth = agent_card.authentication
                if auth.type == AuthenticationType.OAUTH:
                    if not auth.authorization_endpoint:
                        raise ValidationError(f"OAuth sin authorization_endpoint en Agent Card {agent_card.name}")
                    if not auth.token_endpoint:
                        raise ValidationError(f"OAuth sin token_endpoint en Agent Card {agent_card.name}")
            
            self._logger.debug(f"Agent Card {agent_card.name} validado exitosamente")
            
        except Exception as e:
            raise ValidationError(f"Error validando Agent Card {agent_card.name}: {e}")
    
    def export_agent_card(self, agent_name: str, format: str = "json") -> str:
        """
        Exporta Agent Card en formato específico.
        
        Args:
            agent_name: Nombre del agente
            format: Formato de exportación (json, yaml)
            
        Returns:
            Agent Card en formato especificado
            
        Raises:
            A2AProtocolError: Si el agente no existe o hay error exportando
        """
        try:
            agent_card = self.get_agent_card(agent_name)
            if not agent_card:
                raise A2AProtocolError(f"Agent Card no encontrado para agente {agent_name}")
            
            if format.lower() == "json":
                return safe_json_dumps(agent_card.dict())
            elif format.lower() == "yaml":
                import yaml
                return yaml.dump(agent_card.dict(), default_flow_style=False)
            else:
                raise A2AProtocolError(f"Formato de exportación no soportado: {format}")
                
        except Exception as e:
            raise A2AProtocolError(f"Error exportando Agent Card para agente {agent_name}: {e}")
    
    def import_agent_card(self, agent_card_data: Union[str, Dict[str, Any]], format: str = "json") -> AgentCard:
        """
        Importa Agent Card desde formato específico.
        
        Args:
            agent_card_data: Datos del Agent Card
            format: Formato de importación (json, yaml)
            
        Returns:
            Agent Card importado
            
        Raises:
            A2AProtocolError: Si hay error importando
        """
        try:
            if isinstance(agent_card_data, str):
                if format.lower() == "json":
                    import json
                    data = json.loads(agent_card_data)
                elif format.lower() == "yaml":
                    import yaml
                    data = yaml.safe_load(agent_card_data)
                else:
                    raise A2AProtocolError(f"Formato de importación no soportado: {format}")
            else:
                data = agent_card_data
            
            # Crear Agent Card
            agent_card = AgentCard(**data)
            
            # Validar Agent Card
            self._validate_agent_card(agent_card)
            
            # Almacenar Agent Card
            self._agent_cards[agent_card.name] = agent_card
            
            self._logger.info(f"Agent Card importado para agente {agent_card.name}")
            return agent_card
            
        except Exception as e:
            raise A2AProtocolError(f"Error importando Agent Card: {e}")
    
    def get_agent_cards_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen de todos los Agent Cards.
        
        Returns:
            Diccionario con resumen de Agent Cards
        """
        summary = {
            "total_agents": len(self._agent_cards),
            "agents": []
        }
        
        for agent_name, agent_card in self._agent_cards.items():
            summary["agents"].append({
                "name": agent_card.name,
                "version": agent_card.version,
                "skills_count": len(agent_card.skills),
                "authentication_type": agent_card.authentication.type.value if agent_card.authentication else "none",
                "endpoint": agent_card.endpoint
            })
        
        return summary
