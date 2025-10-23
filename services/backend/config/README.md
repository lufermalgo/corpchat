# Backend Configuration

This directory contains configuration files for the backend services.

## Structure

- `models.yaml` - Model configurations and mappings
- `agents.yaml` - Agent metadata and references (NO prompts)
- `prompts.yaml` - System prompts and instructions for all agents
- `deployment.yaml` - Deployment-specific configurations (future)

## Usage

Configuration files are loaded by the backend services to:
- Define available models and their mappings
- Configure agent metadata and capabilities
- Set system prompts and instructions
- Set deployment-specific parameters

## File Responsibilities

### `agents.yaml` - Agent Metadata
- **Purpose**: Agent configuration and metadata
- **Contains**: name, description, capabilities, default_model, prompt_ref
- **NO prompts**: Only references to prompts.yaml

### `prompts.yaml` - System Prompts
- **Purpose**: All system prompts and context
- **Contains**: system prompts, context information
- **Referenced by**: agents.yaml via prompt_ref

## Customization

### Models
To add new models or modify existing configurations:
1. Update `models.yaml`
2. Restart the affected services
3. The changes will be applied automatically

### Agent Behavior
To modify agent behavior:
1. Update `agents.yaml` for metadata (name, capabilities, etc.)
2. Update `prompts.yaml` for system prompts and instructions
3. Restart the affected services

### System Prompts
To customize agent behavior and responses:
1. Edit the `system` prompts in `prompts.yaml`
2. Add `context` information for additional guidance
3. Restart the affected services

### Adding New Agents
1. Add agent metadata to `agents.yaml`
2. Add corresponding prompts to `prompts.yaml`
3. Set `prompt_ref` in agents.yaml to match the key in prompts.yaml

## File Structure

```
config/
├── models.yaml      # Model definitions and mappings
├── agents.yaml      # Agent configurations
├── prompts.yaml     # System prompts and instructions
└── README.md        # This file
```
