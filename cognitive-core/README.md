# Core Cognitivo Universal

**Core Cognitivo Universal para Orquestación Multi-Agente usando Google ADK y A2A Protocol**

## Visión del Proyecto

El Core Cognitivo es una solución universal, agnóstica y replicable que centraliza conocimiento empresarial mediante agentes especializados coordinados por Google ADK y A2A Protocol. Permite la orquestación inteligente de múltiples agentes para generar decisiones estratégicas integradas.

**Principio:** "La arquitectura es universal, los casos de uso son específicos"

## Arquitectura

### Componentes Principales

```
CognitiveCore:
├── Orchestrator (SequentialAgent)
│   ├── ContextAnalyzer (LlmAgent)
│   ├── DomainRouter (LlmAgent) 
│   ├── KnowledgeSynthesizer (LlmAgent)
│   └── DecisionEngine (LlmAgent)
│
├── Specialized Agents (LlmAgent)
│   ├── TerrestrialLogisticsAgent
│   ├── MaritimeLogisticsAgent
│   └── MultimodalIntegrationAgent
│
├── A2A Protocol Layer
│   ├── Agent Cards
│   ├── Agent Skills
│   └── Task Management
│
└── Custom Tools (FunctionTool)
    ├── GPS Fleet Tools
    ├── Route Optimization Tools
    └── Maritime Tools
```

### Tecnologías

- **Google ADK**: LlmAgent, SequentialAgent, FunctionTool, InMemorySessionService
- **A2A Protocol**: Agent Cards, Agent Skills, Task Management
- **Python 3.9+**: Pydantic, PyYAML, pytest
- **Docker**: Desarrollo local y testing

## Caso de Validación: Argos

**Problema:** Transporte terrestre (GPS) y marítimo desconectados en Argos
**Solución:** Core Cognitivo integra ambos mundos para optimización multimodal

### Escenario E2E
- **Input:** "Necesito enviar 8000 toneladas de cemento a Alabama"
- **Output:** Plan multimodal completo con costos, tiempos y fases

## Quick Start

### Prerequisitos
- Python 3.9+
- Docker Desktop
- Google Cloud SDK (para ADK)

### Instalación

```bash
# Clonar repositorio
git clone <repository-url>
cd cognitive-core

# Instalar dependencias
pip install -r requirements.txt

# Configurar entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar tests
python -m pytest tests/ -v
```

### Desarrollo con Docker

```bash
# Construir imagen
docker-compose -f docker/docker-compose.yml build

# Ejecutar tests
docker-compose -f docker/docker-compose.yml up cognitive-core

# Shell interactivo
docker-compose -f docker/docker-compose.yml run cognitive-core-interactive
```

## Estructura del Proyecto

```
cognitive-core/
├── src/
│   ├── core/           # Orchestrator y componentes principales
│   ├── agents/         # Agentes especializados
│   ├── tools/          # Custom tools (FunctionTool)
│   ├── a2a/           # A2A Protocol implementation
│   ├── config/        # Configuration management
│   └── shared/        # Utilities y tipos comunes
├── config/            # Archivos YAML de configuración
├── tests/             # Tests unitarios, integración y E2E
├── docker/            # Docker setup
└── docs/              # Documentación
```

## Desarrollo

### Principios de Desarrollo

- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY**: Don't Repeat Yourself
- **Type Hints**: Python type hints en todas las funciones
- **Testing**: Cobertura > 80%, tests E2E obligatorios
- **Documentation**: Docstrings completos, README actualizado

### Flujo de Desarrollo

1. **Desarrollo Local**: Docker Desktop obligatorio
2. **Testing Real**: Datos reales, no mocks sintéticos
3. **Validación E2E**: Caso Argos como validación principal
4. **Documentación**: PRD, Architecture, Demo guides

## Configuración

### Archivos de Configuración

- `config/core.yaml`: Configuración principal del Core Cognitivo
- `config/agents/`: Configuración específica por agente
- `config/argos/`: Caso de validación Argos

### Variables de Entorno

```bash
# .env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
PROJECT_ID=your-gcp-project
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Testing

### Tipos de Tests

- **Unit Tests**: Componentes individuales
- **Integration Tests**: Interacción entre componentes
- **E2E Tests**: Caso completo Argos

### Ejecutar Tests

```bash
# Todos los tests
python -m pytest tests/ -v

# Tests específicos
python -m pytest tests/unit/ -v
python -m pytest tests/e2e/test_argos_case.py -v

# Con cobertura
python -m pytest tests/ --cov=src --cov-report=html
```

## Caso de Uso: Argos

### Problema Original
- Transporte terrestre (100% GPS) desconectado del marítimo
- Decisiones manuales entre unidades
- Falta de optimización multimodal

### Solución Core Cognitivo
- **TerrestrialLogisticsAgent**: Optimiza transporte plantas → puerto
- **MaritimeLogisticsAgent**: Coordina transporte puerto → destino
- **MultimodalIntegrationAgent**: Integra ambos mundos

### Resultado Esperado
```json
{
  "query": "8000 toneladas de cemento a Alabama",
  "analysis": {
    "terrestrial": {
      "trucks": 8,
      "cost": "$8,000",
      "time": "2 días"
    },
    "maritime": {
      "vessel": "MV Argos Carrier",
      "cost": "$37,000", 
      "time": "10 días"
    }
  },
  "decision": {
    "total_cost": "$45,000",
    "total_time": "12 días",
    "confidence": 94
  }
}
```

## Contribución

### Estándares de Código

- **Nomenclatura**: PascalCase para clases, snake_case para funciones
- **Docstrings**: Descripción, Args, Returns
- **Logging**: Usar `logging.getLogger(__name__)`
- **Error Handling**: Excepciones específicas, no genéricas

### Proceso

1. Fork del repositorio
2. Feature branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Add nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Pull Request

## Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

## Contacto

**CorpChat Development Team**
- Email: dev@corpchat.com
- Proyecto: Core Cognitivo Universal
