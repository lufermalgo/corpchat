"""
CLI para Personalización del Cognitive Core.

Herramientas de línea de comandos para crear agentes, tools
y personalizar el sistema multi-agente.
"""

import click
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List

from ..core.cognitive_core import CognitiveCore
from ..core.agent_manager import AgentManager
from ..shared.types import CoreConfig, AgentConfig, ToolConfig
from ..shared.utils import get_logger


@click.group()
def cli():
    """CLI para personalización del Cognitive Core."""
    pass


@cli.command()
@click.option('--name', required=True, help='Nombre del agente')
@click.option('--description', required=True, help='Descripción del agente')
@click.option('--model', default='gemini-2.0-flash', help='Modelo a usar')
@click.option('--instruction', required=True, help='Instrucción del agente')
@click.option('--skills', help='Skills del agente (JSON)')
@click.option('--tools', help='Tools del agente (JSON)')
@click.option('--output', help='Archivo de salida')
def create_agent(name: str, description: str, model: str, instruction: str, 
                skills: str, tools: str, output: str):
    """Crea un nuevo agente personalizado."""
    
    # Parsear skills y tools
    skills_list = json.loads(skills) if skills else []
    tools_list = json.loads(tools) if tools else []
    
    # Crear configuración del agente
    agent_config = AgentConfig(
        name=name,
        description=description,
        model=model,
        instruction=instruction,
        skills=skills_list,
        tools=tools_list
    )
    
    # Crear archivo de configuración
    config_data = {
        "agent": {
            "name": agent_config.name,
            "description": agent_config.description,
            "model": agent_config.model,
            "instruction": agent_config.instruction,
            "skills": agent_config.skills,
            "tools": [tool.name for tool in agent_config.tools]
        }
    }
    
    # Guardar configuración
    output_file = output or f"{name}_agent.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    click.echo(f"Agente '{name}' creado en {output_file}")


@cli.command()
@click.option('--name', required=True, help='Nombre del tool')
@click.option('--description', required=True, help='Descripción del tool')
@click.option('--function', required=True, help='Función del tool')
@click.option('--input-schema', help='Schema de entrada (JSON)')
@click.option('--output-schema', help='Schema de salida (JSON)')
@click.option('--output', help='Archivo de salida')
def create_tool(name: str, description: str, function: str, 
               input_schema: str, output_schema: str, output: str):
    """Crea un nuevo tool personalizado."""
    
    # Parsear schemas
    input_schema_dict = json.loads(input_schema) if input_schema else {}
    output_schema_dict = json.loads(output_schema) if output_schema else {}
    
    # Crear configuración del tool
    tool_config = ToolConfig(
        name=name,
        description=description,
        function=function,
        input_schema=input_schema_dict,
        output_schema=output_schema_dict
    )
    
    # Crear archivo de configuración
    config_data = {
        "tool": {
            "name": tool_config.name,
            "description": tool_config.description,
            "function": tool_config.function,
            "input_schema": tool_config.input_schema,
            "output_schema": tool_config.output_schema
        }
    }
    
    # Guardar configuración
    output_file = output or f"{name}_tool.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    click.echo(f"Tool '{name}' creado en {output_file}")


@cli.command()
@click.option('--config', required=True, help='Archivo de configuración del core')
@click.option('--port', default=8000, help='Puerto del servidor')
@click.option('--host', default='0.0.0.0', help='Host del servidor')
def start_server(config: str, port: int, host: str):
    """Inicia el servidor del Cognitive Core."""
    
    # Cargar configuración
    with open(config, 'r') as f:
        config_data = yaml.safe_load(f)
    
    core_config = CoreConfig(**config_data['core'])
    
    # Crear core
    core = CognitiveCore(core_config)
    
    click.echo(f"Iniciando Cognitive Core en {host}:{port}")
    click.echo(f"Configuración: {config}")
    
    # Aquí se iniciaría el servidor real
    # Por ahora solo mostramos la información
    click.echo("Servidor iniciado (modo simulación)")


@cli.command()
@click.option('--config', required=True, help='Archivo de configuración del core')
def validate_config(config: str):
    """Valida la configuración del core."""
    
    try:
        # Cargar configuración
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Validar configuración
        core_config = CoreConfig(**config_data['core'])
        
        click.echo("✅ Configuración válida")
        click.echo(f"Core: {core_config.name}")
        click.echo(f"Modelo: {core_config.default_model}")
        click.echo(f"Versión: {core_config.version}")
        
    except Exception as e:
        click.echo(f"❌ Error en configuración: {e}")


@cli.command()
@click.option('--config', required=True, help='Archivo de configuración del core')
def list_agents(config: str):
    """Lista los agentes disponibles."""
    
    try:
        # Cargar configuración
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        
        core_config = CoreConfig(**config_data['core'])
        
        # Crear core
        core = CognitiveCore(core_config)
        
        # Obtener información de agentes
        agent_cards = core.get_agent_cards()
        
        if agent_cards:
            click.echo("Agentes disponibles:")
            for card in agent_cards:
                click.echo(f"  - {card['name']}: {card['description']}")
        else:
            click.echo("No hay agentes registrados")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.command()
@click.option('--config', required=True, help='Archivo de configuración del core')
def info(config: str):
    """Muestra información del core."""
    
    try:
        # Cargar configuración
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        
        core_config = CoreConfig(**config_data['core'])
        
        # Crear core
        core = CognitiveCore(core_config)
        
        # Obtener información
        info = core.get_core_info()
        
        click.echo("Información del Cognitive Core:")
        click.echo(f"  Nombre: {info['name']}")
        click.echo(f"  Descripción: {info['description']}")
        click.echo(f"  Modelo: {info['model']}")
        click.echo(f"  Agentes: {info['agents_count']}")
        click.echo(f"  Capacidades del pipeline: {', '.join(info['pipeline_capabilities'])}")
        click.echo(f"  Estrategias de orquestación: {', '.join(info['orchestration_strategies'])}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")


if __name__ == '__main__':
    cli()
