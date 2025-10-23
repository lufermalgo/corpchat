# services/backend/src/shared/config.py

import os
import yaml
from pathlib import Path

# --- Configuration ---
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
PROJECT_PREFIX = os.environ.get("PROJECT_PREFIX", "mychat")

# Configuration file paths
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
MODELS_CONFIG_PATH = CONFIG_DIR / "models.yaml"
AGENTS_CONFIG_PATH = CONFIG_DIR / "agents.yaml"
PROMPTS_CONFIG_PATH = CONFIG_DIR / "prompts.yaml"

def load_yaml_config(config_path: Path) -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        print(f"Warning: Config file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"Error loading YAML config {config_path}: {e}")
        return {}

def get_model_config() -> dict:
    """Get model configuration from YAML file"""
    config = load_yaml_config(MODELS_CONFIG_PATH)
    return config.get('models', {})

def get_agent_config() -> dict:
    """Get agent configuration from YAML file"""
    config = load_yaml_config(AGENTS_CONFIG_PATH)
    return config.get('agents', {})

def get_orchestrator_config() -> dict:
    """Get orchestrator configuration from YAML file"""
    config = load_yaml_config(MODELS_CONFIG_PATH)
    return config.get('orchestrator', {})

def get_prompts_config() -> dict:
    """Get prompts configuration from YAML file"""
    config = load_yaml_config(PROMPTS_CONFIG_PATH)
    return config.get('prompts', {})

# Load configurations dynamically from YAML files
MODEL_CONFIG = get_model_config()
AGENT_CONFIG = get_agent_config()
ORCHESTRATOR_CONFIG = get_orchestrator_config()
PROMPTS_CONFIG = get_prompts_config()
