# Análisis: Sistema de Gestión de Agentes Especializados

## Problema Identificado

La arquitectura actual implementa un sistema de "detección dinámica" de agentes que **NO es escalable** para agentes especializados reales. Los problemas identificados son:

### 1. **Arquitectura Actual Problemática**
- **Detección automática**: El orchestrator "detecta" qué agente usar basado en palabras clave
- **Un solo contenedor**: Solo existe `agent-generalist`, otros agentes son solo configuración YAML
- **Routing automático**: No hay selección explícita del usuario
- **Falta de herramientas**: No hay sistema para tools específicas de cada agente

### 2. **Lo que Necesitamos para Agentes Especializados Reales**

#### **Selección Explícita del Usuario**
- Los agentes especializados deben aparecer en el selector de modelos de la UI
- Formato: `agent-data-analyst`, `agent-code-reviewer`, `agent-customer-support`
- El usuario selecciona explícitamente qué agente usar

#### **Contenedores Dedicados**
- Cada agente especializado debe tener su propio contenedor Docker
- Cada contenedor debe tener sus herramientas específicas instaladas
- Ejemplo: `agent-data-analyst` tendría pandas, matplotlib, etc.

#### **Configuración Completa**
- Cada agente debe tener su configuración completa en YAML:
  - System prompts especializados
  - Tools disponibles
  - Capabilities específicas
  - Modelos preferidos
  - Configuración de A2A

#### **A2A Real**
- Comunicación real entre orchestrator y agentes especializados
- Cada agente debe implementar el protocolo A2A correctamente
- Tools específicas deben estar disponibles via A2A

## Solución Propuesta

### **Fase 1: Análisis y Diseño**
1. **Estudiar Open WebUI**: Analizar cómo maneja la importación/exportación de modelos
2. **Definir Agent Packages**: Formato estándar para empaquetar agentes (YAML + código + tools)
3. **Diseñar Sistema de Contenedores**: Cómo crear contenedores dinámicos para agentes

### **Fase 2: Implementación**
1. **Sistema de Gestión**: CRUD para agentes especializados
2. **UI Modificada**: Selector de modelos que incluya agentes especializados
3. **Routing Basado en Selección**: Orchestrator routea basado en selección del usuario
4. **A2A Real**: Comunicación real entre orchestrator y agentes especializados

### **Fase 3: Agentes de Ejemplo**
1. **Agent Data Analyst**: Análisis estadístico, visualización, reportes
2. **Agent Code Reviewer**: Análisis de código, seguridad, calidad
3. **Agent Customer Support**: Atención al cliente, escalación, tickets

## Arquitectura Propuesta

```
UI (Open WebUI)
├── Modelos LLM: gemini-fast, gemini-thinking, gemini-images
└── Agentes Especializados: agent-data-analyst, agent-code-reviewer, etc.

Gateway (Nginx)
└── Routea a Orchestrator

Orchestrator (ADK)
├── Recibe selección del usuario
├── Routea a agente correspondiente
└── Implementa A2A real

Agentes Especializados (Contenedores Dedicados)
├── agent-data-analyst (Puerto 8002)
├── agent-code-reviewer (Puerto 8003)
└── agent-customer-support (Puerto 8004)
```

## Beneficios de la Solución

1. **Escalabilidad**: Fácil agregar nuevos agentes sin modificar código
2. **Especialización**: Cada agente tiene sus herramientas específicas
3. **Selección Explícita**: El usuario controla qué agente usar
4. **A2A Real**: Comunicación real entre agentes
5. **Gestión Dinámica**: Sistema para importar/exportar agentes
6. **Mantenibilidad**: Cada agente es independiente

## Próximos Pasos

1. **Completar Fase 1 Actual**: Terminar la implementación del core con agent-generalist
2. **Análisis Detallado**: Estudiar Open WebUI y definir Agent Packages
3. **Diseño de Arquitectura**: Diseñar sistema de contenedores dinámicos
4. **Implementación**: Crear sistema de gestión de agentes especializados

## Conclusión

La arquitectura actual es un buen punto de partida para el core, pero **NO es escalable** para agentes especializados reales. Se requiere un sistema completo de gestión de agentes que permita:

- Selección explícita del usuario
- Contenedores dedicados para cada agente
- Configuración completa en YAML
- A2A real entre agentes
- Sistema de gestión dinámico

Este análisis debe ser considerado para la siguiente fase del proyecto.
