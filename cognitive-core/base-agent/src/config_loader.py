"""Configuration loader implementation."""

import os
import yaml
from typing import Dict, Any, Optional
from .interfaces import IConfigLoader


class YAMLConfigLoader(IConfigLoader):
    """YAML-based configuration loader (Single Responsibility Principle)."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config: Optional[Dict[str, Any]] = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if self._config is None:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self._config = yaml.safe_load(file)
            except FileNotFoundError:
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML configuration: {e}")
        
        return self._config
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        config = self.load_config()
        
        # Support dot notation for nested keys
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value


class EnvironmentConfigLoader(IConfigLoader):
    """Environment variables configuration loader."""
    
    def __init__(self, prefix: str = ""):
        self.prefix = prefix
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        for key, value in os.environ.items():
            if self.prefix and not key.startswith(self.prefix):
                continue
            
            # Remove prefix if present
            clean_key = key[len(self.prefix):] if self.prefix else key
            clean_key = clean_key.lower().replace('_', '.')
            
            # Convert string values to appropriate types
            config[clean_key] = self._convert_value(value)
        
        return config
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        config = self.load_config()
        return config.get(key, default)
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Numeric conversion
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        return value


class CompositeConfigLoader(IConfigLoader):
    """Composite configuration loader that combines multiple sources."""
    
    def __init__(self, loaders: list[IConfigLoader]):
        self.loaders = loaders
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from all sources."""
        config = {}
        
        for loader in self.loaders:
            try:
                loader_config = loader.load_config()
                config.update(loader_config)
            except Exception as e:
                print(f"Warning: Failed to load config from {type(loader).__name__}: {e}")
        
        return config
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value from first available source."""
        for loader in self.loaders:
            try:
                value = loader.get_value(key, None)
                if value is not None:
                    return value
            except Exception:
                continue
        
        return default
