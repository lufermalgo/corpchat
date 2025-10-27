"""
Context Manager para gestión de contextos según A2A Protocol.

Este módulo implementa la gestión de contextos para agrupación lógica
de tareas relacionadas según la especificación oficial del protocolo A2A.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..shared.exceptions import A2AProtocolError, ValidationError
from ..shared.utils import get_logger, get_timestamp
from .task_manager import TaskManager, TaskInfo


class ContextInfo:
    """
    Información de contexto para agrupación de tareas.
    
    Representa un contexto lógico que agrupa tareas relacionadas
    según la especificación A2A Protocol.
    """
    
    def __init__(self, 
                 context_id: str,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Inicializa información de contexto.
        
        Args:
            context_id: ID único del contexto
            name: Nombre del contexto (opcional)
            description: Descripción del contexto (opcional)
            metadata: Metadatos adicionales (opcional)
        """
        self.context_id = context_id
        self.name = name or f"Context-{context_id[:8]}"
        self.description = description or f"Contexto para agrupación de tareas relacionadas"
        self.metadata = metadata or {}
        self.created_at = get_timestamp()
        self.updated_at = get_timestamp()
        self.task_ids: List[str] = []
    
    def add_task(self, task_id: str) -> None:
        """
        Agrega una tarea al contexto.
        
        Args:
            task_id: ID de la tarea
        """
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)
            self.updated_at = get_timestamp()
    
    def remove_task(self, task_id: str) -> bool:
        """
        Elimina una tarea del contexto.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            True si se eliminó exitosamente
        """
        if task_id in self.task_ids:
            self.task_ids.remove(task_id)
            self.updated_at = get_timestamp()
            return True
        return False
    
    def get_task_count(self) -> int:
        """
        Obtiene el número de tareas en el contexto.
        
        Returns:
            Número de tareas
        """
        return len(self.task_ids)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte a diccionario.
        
        Returns:
            Diccionario con información del contexto
        """
        return {
            "context_id": self.context_id,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "task_count": self.get_task_count(),
            "task_ids": self.task_ids.copy()
        }


class ContextManager:
    """
    Gestor de contextos para el protocolo A2A.
    
    Maneja la creación, gestión y agrupación de contextos
    para tareas relacionadas según la especificación A2A.
    """
    
    def __init__(self, task_manager: Optional[TaskManager] = None):
        """
        Inicializa el gestor de contextos.
        
        Args:
            task_manager: Gestor de tareas (opcional)
        """
        self._logger = get_logger(__name__)
        self._contexts: Dict[str, ContextInfo] = {}
        self._task_manager = task_manager
        self._logger.info("ContextManager inicializado")
    
    def create_context(self, 
                      name: Optional[str] = None,
                      description: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None,
                      context_id: Optional[str] = None) -> ContextInfo:
        """
        Crea un nuevo contexto.
        
        Args:
            name: Nombre del contexto (opcional)
            description: Descripción del contexto (opcional)
            metadata: Metadatos adicionales (opcional)
            context_id: ID personalizado del contexto (opcional)
            
        Returns:
            Información del contexto creado
            
        Raises:
            A2AProtocolError: Si hay error creando el contexto
        """
        try:
            # Generar ID de contexto si no se proporciona
            if not context_id:
                context_id = str(uuid.uuid4())
            
            # Verificar que el contexto no exista
            if context_id in self._contexts:
                raise A2AProtocolError(f"Contexto ya existe: {context_id}")
            
            # Crear contexto
            context_info = ContextInfo(
                context_id=context_id,
                name=name,
                description=description,
                metadata=metadata
            )
            
            # Validar contexto
            self._validate_context_info(context_info)
            
            # Almacenar contexto
            self._contexts[context_id] = context_info
            
            self._logger.info(f"Contexto {context_id} creado")
            return context_info
            
        except Exception as e:
            raise A2AProtocolError(f"Error creando contexto: {e}")
    
    def get_context(self, context_id: str) -> Optional[ContextInfo]:
        """
        Obtiene información de un contexto.
        
        Args:
            context_id: ID del contexto
            
        Returns:
            Información del contexto o None
        """
        return self._contexts.get(context_id)
    
    def get_all_contexts(self) -> Dict[str, ContextInfo]:
        """
        Obtiene todos los contextos.
        
        Returns:
            Diccionario con todos los contextos
        """
        return self._contexts.copy()
    
    def update_context(self, 
                      context_id: str, 
                      updates: Dict[str, Any]) -> ContextInfo:
        """
        Actualiza un contexto existente.
        
        Args:
            context_id: ID del contexto
            updates: Actualizaciones a aplicar
            
        Returns:
            Información del contexto actualizado
            
        Raises:
            A2AProtocolError: Si el contexto no existe o hay error actualizando
        """
        try:
            if context_id not in self._contexts:
                raise A2AProtocolError(f"Contexto no encontrado: {context_id}")
            
            context_info = self._contexts[context_id]
            
            # Aplicar actualizaciones
            if "name" in updates:
                context_info.name = updates["name"]
            
            if "description" in updates:
                context_info.description = updates["description"]
            
            if "metadata" in updates:
                context_info.metadata.update(updates["metadata"])
            
            context_info.updated_at = get_timestamp()
            
            # Validar contexto actualizado
            self._validate_context_info(context_info)
            
            self._logger.info(f"Contexto {context_id} actualizado")
            return context_info
            
        except Exception as e:
            raise A2AProtocolError(f"Error actualizando contexto {context_id}: {e}")
    
    def delete_context(self, context_id: str, delete_tasks: bool = False) -> bool:
        """
        Elimina un contexto.
        
        Args:
            context_id: ID del contexto
            delete_tasks: Si eliminar también las tareas del contexto
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            if context_id not in self._contexts:
                return False
            
            context_info = self._contexts[context_id]
            
            # Eliminar tareas si se solicita
            if delete_tasks and self._task_manager:
                for task_id in context_info.task_ids:
                    self._task_manager.delete_task(task_id)
            
            # Eliminar contexto
            del self._contexts[context_id]
            
            self._logger.info(f"Contexto {context_id} eliminado")
            return True
            
        except Exception as e:
            self._logger.error(f"Error eliminando contexto {context_id}: {e}")
            return False
    
    def add_task_to_context(self, context_id: str, task_id: str) -> bool:
        """
        Agrega una tarea a un contexto.
        
        Args:
            context_id: ID del contexto
            task_id: ID de la tarea
            
        Returns:
            True si se agregó exitosamente
        """
        try:
            if context_id not in self._contexts:
                raise A2AProtocolError(f"Contexto no encontrado: {context_id}")
            
            context_info = self._contexts[context_id]
            context_info.add_task(task_id)
            
            self._logger.debug(f"Tarea {task_id} agregada al contexto {context_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Error agregando tarea {task_id} al contexto {context_id}: {e}")
            return False
    
    def remove_task_from_context(self, context_id: str, task_id: str) -> bool:
        """
        Elimina una tarea de un contexto.
        
        Args:
            context_id: ID del contexto
            task_id: ID de la tarea
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            if context_id not in self._contexts:
                return False
            
            context_info = self._contexts[context_id]
            return context_info.remove_task(task_id)
            
        except Exception as e:
            self._logger.error(f"Error eliminando tarea {task_id} del contexto {context_id}: {e}")
            return False
    
    def get_context_tasks(self, context_id: str) -> List[TaskInfo]:
        """
        Obtiene todas las tareas de un contexto.
        
        Args:
            context_id: ID del contexto
            
        Returns:
            Lista de tareas del contexto
        """
        try:
            if context_id not in self._contexts:
                return []
            
            if not self._task_manager:
                return []
            
            context_info = self._contexts[context_id]
            tasks = []
            
            for task_id in context_info.task_ids:
                task_info = self._task_manager.get_task(task_id)
                if task_info:
                    tasks.append(task_info)
            
            return tasks
            
        except Exception as e:
            self._logger.error(f"Error obteniendo tareas del contexto {context_id}: {e}")
            return []
    
    def get_context_statistics(self, context_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un contexto.
        
        Args:
            context_id: ID del contexto
            
        Returns:
            Diccionario con estadísticas del contexto
        """
        try:
            if context_id not in self._contexts:
                return {}
            
            context_info = self._contexts[context_id]
            tasks = self.get_context_tasks(context_id)
            
            # Contar tareas por estado
            status_counts = {}
            for task in tasks:
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "context_id": context_id,
                "name": context_info.name,
                "description": context_info.description,
                "total_tasks": len(tasks),
                "status_counts": status_counts,
                "created_at": context_info.created_at,
                "updated_at": context_info.updated_at,
                "metadata": context_info.metadata
            }
            
        except Exception as e:
            self._logger.error(f"Error obteniendo estadísticas del contexto {context_id}: {e}")
            return {}
    
    def get_all_contexts_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de todos los contextos.
        
        Returns:
            Diccionario con estadísticas generales
        """
        try:
            total_contexts = len(self._contexts)
            total_tasks = sum(len(context.task_ids) for context in self._contexts.values())
            
            context_stats = []
            for context_id in self._contexts:
                stats = self.get_context_statistics(context_id)
                if stats:
                    context_stats.append(stats)
            
            return {
                "total_contexts": total_contexts,
                "total_tasks": total_tasks,
                "contexts": context_stats
            }
            
        except Exception as e:
            self._logger.error(f"Error obteniendo estadísticas generales: {e}")
            return {}
    
    def _validate_context_info(self, context_info: ContextInfo) -> None:
        """
        Valida información de contexto.
        
        Args:
            context_info: Información de contexto a validar
            
        Raises:
            ValidationError: Si la información es inválida
        """
        try:
            if not context_info.context_id:
                raise ValidationError("Contexto sin ID")
            
            if not context_info.name:
                raise ValidationError(f"Contexto {context_info.context_id} sin nombre")
            
            if not context_info.description:
                raise ValidationError(f"Contexto {context_info.context_id} sin descripción")
            
            self._logger.debug(f"Contexto {context_info.context_id} validado exitosamente")
            
        except Exception as e:
            raise ValidationError(f"Error validando contexto {context_info.context_id}: {e}")
    
    def cleanup_empty_contexts(self) -> int:
        """
        Limpia contextos vacíos.
        
        Returns:
            Número de contextos eliminados
        """
        try:
            empty_contexts = []
            
            for context_id, context_info in self._contexts.items():
                if context_info.get_task_count() == 0:
                    empty_contexts.append(context_id)
            
            deleted_count = 0
            for context_id in empty_contexts:
                if self.delete_context(context_id):
                    deleted_count += 1
            
            self._logger.info(f"Limpieza completada: {deleted_count} contextos vacíos eliminados")
            return deleted_count
            
        except Exception as e:
            self._logger.error(f"Error en limpieza de contextos: {e}")
            return 0
