"""
Utilidades comunes para el Core Cognitivo.

Este módulo contiene funciones de utilidad reutilizables que siguen principios DRY
y facilitan el desarrollo de componentes del sistema.
"""

import logging
import time
import json
from typing import Any, Dict, Optional, Union
from datetime import datetime
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado.
    
    Args:
        name: Nombre del módulo (usar __name__)
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def measure_time(func):
    """
    Decorator para medir tiempo de ejecución de funciones.
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada con medición de tiempo
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger = get_logger(func.__module__)
        logger.info(f"Función {func.__name__} ejecutada en {execution_time:.2f} segundos")
        
        return result
    return wrapper


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Carga JSON de forma segura con valor por defecto.
    
    Args:
        json_str: String JSON a parsear
        default: Valor por defecto si falla el parsing
        
    Returns:
        Objeto parseado o valor por defecto
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger = get_logger(__name__)
        logger.warning(f"Error parseando JSON: {e}")
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Serializa objeto a JSON de forma segura.
    
    Args:
        obj: Objeto a serializar
        default: String por defecto si falla la serialización
        
    Returns:
        String JSON o valor por defecto
    """
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        logger = get_logger(__name__)
        logger.warning(f"Error serializando JSON: {e}")
        return default


def get_timestamp() -> str:
    """
    Obtiene timestamp actual en formato ISO.
    
    Returns:
        Timestamp en formato ISO string
    """
    return datetime.utcnow().isoformat() + "Z"


def validate_file_path(file_path: Union[str, Path]) -> Path:
    """
    Valida y convierte path de archivo a Path object.
    
    Args:
        file_path: Path como string o Path object
        
    Returns:
        Path object validado
        
    Raises:
        FileNotFoundError: Si el archivo no existe
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    return path


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combina dos diccionarios de forma recursiva.
    
    Args:
        dict1: Primer diccionario
        dict2: Segundo diccionario
        
    Returns:
        Diccionario combinado
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca string a longitud máxima con sufijo.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a agregar
        
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Formatea cantidad como moneda.
    
    Args:
        amount: Cantidad a formatear
        currency: Código de moneda
        
    Returns:
        String formateado como moneda
    """
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_duration(seconds: float) -> str:
    """
    Formatea duración en segundos a formato legible.
    
    Args:
        seconds: Duración en segundos
        
    Returns:
        String formateado de duración
    """
    if seconds < 60:
        return f"{seconds:.1f} segundos"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutos"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} horas"
