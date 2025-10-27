"""
Task Manager para gestión de estados de tareas según A2A Protocol.

Este módulo implementa la gestión de tareas y sus estados según la especificación
oficial del protocolo A2A para coordinación entre agentes.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

from ..shared.types import TaskInfo, TaskStatus
from ..shared.exceptions import A2AProtocolError, ValidationError
from ..shared.utils import get_logger, get_timestamp


class TaskManager:
    """
    Gestor de tareas para el protocolo A2A.
    
    Maneja el ciclo de vida de tareas, estados y coordinación
    entre agentes según la especificación oficial A2A.
    """
    
    def __init__(self):
        """Inicializa el gestor de tareas."""
        self._logger = get_logger(__name__)
        self._tasks: Dict[str, TaskInfo] = {}
        self._contexts: Dict[str, List[str]] = {}  # context_id -> task_ids
        self._logger.info("TaskManager inicializado")
    
    def create_task(self, 
                   context_id: str,
                   skill_id: str,
                   input_data: Dict[str, Any],
                   task_id: Optional[str] = None) -> TaskInfo:
        """
        Crea una nueva tarea.
        
        Args:
            context_id: ID del contexto
            skill_id: ID del skill a ejecutar
            input_data: Datos de entrada
            task_id: ID de tarea personalizado (opcional)
            
        Returns:
            Información de la tarea creada
            
        Raises:
            A2AProtocolError: Si hay error creando la tarea
        """
        try:
            # Generar ID de tarea si no se proporciona
            if not task_id:
                task_id = str(uuid.uuid4())
            
            # Crear información de tarea
            task_info = TaskInfo(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus.PENDING,
                skill_id=skill_id,
                input_data=input_data,
                created_at=get_timestamp()
            )
            
            # Validar tarea
            self._validate_task_info(task_info)
            
            # Almacenar tarea
            self._tasks[task_id] = task_info
            
            # Agregar a contexto
            if context_id not in self._contexts:
                self._contexts[context_id] = []
            self._contexts[context_id].append(task_id)
            
            self._logger.info(f"Tarea {task_id} creada en contexto {context_id}")
            return task_info
            
        except Exception as e:
            raise A2AProtocolError(f"Error creando tarea: {e}")
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """
        Obtiene información de una tarea.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Información de la tarea o None
        """
        return self._tasks.get(task_id)
    
    def get_tasks_by_context(self, context_id: str) -> List[TaskInfo]:
        """
        Obtiene todas las tareas de un contexto.
        
        Args:
            context_id: ID del contexto
            
        Returns:
            Lista de tareas del contexto
        """
        task_ids = self._contexts.get(context_id, [])
        return [self._tasks[task_id] for task_id in task_ids if task_id in self._tasks]
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[TaskInfo]:
        """
        Obtiene todas las tareas con un estado específico.
        
        Args:
            status: Estado de las tareas
            
        Returns:
            Lista de tareas con el estado especificado
        """
        return [task for task in self._tasks.values() if task.status == status]
    
    def update_task_status(self, 
                          task_id: str, 
                          status: TaskStatus,
                          output_data: Optional[Dict[str, Any]] = None,
                          error_message: Optional[str] = None) -> TaskInfo:
        """
        Actualiza el estado de una tarea.
        
        Args:
            task_id: ID de la tarea
            status: Nuevo estado
            output_data: Datos de salida (opcional)
            error_message: Mensaje de error (opcional)
            
        Returns:
            Información de tarea actualizada
            
        Raises:
            A2AProtocolError: Si la tarea no existe o hay error actualizando
        """
        try:
            if task_id not in self._tasks:
                raise A2AProtocolError(f"Tarea no encontrada: {task_id}")
            
            task_info = self._tasks[task_id]
            
            # Actualizar campos
            task_info.status = status
            task_info.updated_at = get_timestamp()
            
            if output_data is not None:
                task_info.output_data = output_data
            
            if error_message is not None:
                task_info.error_message = error_message
            
            # Validar transición de estado
            self._validate_status_transition(task_info.status, status)
            
            self._logger.info(f"Tarea {task_id} actualizada a estado {status.value}")
            return task_info
            
        except Exception as e:
            raise A2AProtocolError(f"Error actualizando estado de tarea {task_id}: {e}")
    
    def complete_task(self, task_id: str, output_data: Dict[str, Any]) -> TaskInfo:
        """
        Marca una tarea como completada.
        
        Args:
            task_id: ID de la tarea
            output_data: Datos de salida
            
        Returns:
            Información de tarea completada
        """
        return self.update_task_status(task_id, TaskStatus.COMPLETED, output_data=output_data)
    
    def fail_task(self, task_id: str, error_message: str) -> TaskInfo:
        """
        Marca una tarea como fallida.
        
        Args:
            task_id: ID de la tarea
            error_message: Mensaje de error
            
        Returns:
            Información de tarea fallida
        """
        return self.update_task_status(task_id, TaskStatus.FAILED, error_message=error_message)
    
    def start_task(self, task_id: str) -> TaskInfo:
        """
        Marca una tarea como en progreso.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Información de tarea en progreso
        """
        return self.update_task_status(task_id, TaskStatus.IN_PROGRESS)
    
    def require_auth_task(self, task_id: str, auth_message: str = "Autenticación requerida") -> TaskInfo:
        """
        Marca una tarea como requeriendo autenticación.
        
        Args:
            task_id: ID de la tarea
            auth_message: Mensaje de autenticación
            
        Returns:
            Información de tarea con requerimiento de autenticación
        """
        return self.update_task_status(task_id, TaskStatus.AUTH_REQUIRED, error_message=auth_message)
    
    def delete_task(self, task_id: str) -> bool:
        """
        Elimina una tarea.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            if task_id not in self._tasks:
                return False
            
            task_info = self._tasks[task_id]
            context_id = task_info.context_id
            
            # Eliminar de contexto
            if context_id in self._contexts:
                if task_id in self._contexts[context_id]:
                    self._contexts[context_id].remove(task_id)
                
                # Eliminar contexto si está vacío
                if not self._contexts[context_id]:
                    del self._contexts[context_id]
            
            # Eliminar tarea
            del self._tasks[task_id]
            
            self._logger.info(f"Tarea {task_id} eliminada")
            return True
            
        except Exception as e:
            self._logger.error(f"Error eliminando tarea {task_id}: {e}")
            return False
    
    def delete_context(self, context_id: str) -> int:
        """
        Elimina todas las tareas de un contexto.
        
        Args:
            context_id: ID del contexto
            
        Returns:
            Número de tareas eliminadas
        """
        try:
            task_ids = self._contexts.get(context_id, [])
            deleted_count = 0
            
            for task_id in task_ids:
                if self.delete_task(task_id):
                    deleted_count += 1
            
            self._logger.info(f"Contexto {context_id} eliminado, {deleted_count} tareas eliminadas")
            return deleted_count
            
        except Exception as e:
            self._logger.error(f"Error eliminando contexto {context_id}: {e}")
            return 0
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de tareas.
        
        Returns:
            Diccionario con estadísticas
        """
        total_tasks = len(self._tasks)
        total_contexts = len(self._contexts)
        
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len(self.get_tasks_by_status(status))
        
        return {
            "total_tasks": total_tasks,
            "total_contexts": total_contexts,
            "status_counts": status_counts,
            "contexts": list(self._contexts.keys())
        }
    
    def _validate_task_info(self, task_info: TaskInfo) -> None:
        """
        Valida información de tarea.
        
        Args:
            task_info: Información de tarea a validar
            
        Raises:
            ValidationError: Si la información es inválida
        """
        try:
            if not task_info.task_id:
                raise ValidationError("Tarea sin ID")
            
            if not task_info.context_id:
                raise ValidationError(f"Tarea {task_info.task_id} sin context_id")
            
            if not task_info.skill_id:
                raise ValidationError(f"Tarea {task_info.task_id} sin skill_id")
            
            if not task_info.input_data:
                raise ValidationError(f"Tarea {task_info.task_id} sin input_data")
            
            self._logger.debug(f"Tarea {task_info.task_id} validada exitosamente")
            
        except Exception as e:
            raise ValidationError(f"Error validando tarea {task_info.task_id}: {e}")
    
    def _validate_status_transition(self, current_status: TaskStatus, new_status: TaskStatus) -> None:
        """
        Valida transición de estado de tarea.
        
        Args:
            current_status: Estado actual
            new_status: Nuevo estado
            
        Raises:
            ValidationError: Si la transición no es válida
        """
        # Definir transiciones válidas
        valid_transitions = {
            TaskStatus.PENDING: [TaskStatus.IN_PROGRESS, TaskStatus.FAILED, TaskStatus.AUTH_REQUIRED],
            TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.AUTH_REQUIRED],
            TaskStatus.AUTH_REQUIRED: [TaskStatus.IN_PROGRESS, TaskStatus.FAILED],
            TaskStatus.COMPLETED: [],  # Estado final
            TaskStatus.FAILED: []      # Estado final
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f"Transición de estado inválida: {current_status.value} -> {new_status.value}"
            )
    
    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        Limpia tareas antiguas.
        
        Args:
            max_age_hours: Edad máxima en horas
            
        Returns:
            Número de tareas eliminadas
        """
        try:
            from datetime import datetime, timedelta
            
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            deleted_count = 0
            
            tasks_to_delete = []
            for task_id, task_info in self._tasks.items():
                if task_info.created_at:
                    try:
                        created_time = datetime.fromisoformat(task_info.created_at.replace('Z', '+00:00'))
                        if created_time < cutoff_time:
                            tasks_to_delete.append(task_id)
                    except ValueError:
                        # Si no se puede parsear la fecha, mantener la tarea
                        continue
            
            for task_id in tasks_to_delete:
                if self.delete_task(task_id):
                    deleted_count += 1
            
            self._logger.info(f"Limpieza completada: {deleted_count} tareas eliminadas")
            return deleted_count
            
        except Exception as e:
            self._logger.error(f"Error en limpieza de tareas: {e}")
            return 0
