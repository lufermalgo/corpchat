# 🧠 Cognitive Core - Arquitectura Multi-Agente

## 🎯 **Principios Arquitectónicos**

Esta arquitectura sigue los principios **SOLID** y **DRY** para crear un ecosistema escalable de agentes:

- **🔄 DRY (Don't Repeat Yourself)**: Componentes compartidos reutilizables
- **📦 SRP (Single Responsibility)**: Cada componente tiene una responsabilidad específica
- **🔧 OCP (Open/Closed)**: Extensible sin modificar código existente
- **🔗 LSP (Liskov Substitution)**: Interfaces intercambiables
- **🎯 ISP (Interface Segregation)**: Interfaces específicas y cohesivas
- **⬆️ DIP (Dependency Inversion)**: Dependencias de abstracciones, no implementaciones

## 📁 **Estructura del Proyecto**

```
cognitive-core/
├── shared/                          # 🔄 Componentes compartidos
│   ├── docker/
│   │   ├── Dockerfile.base          # Dockerfile base para todos los agentes
│   │   ├── docker-compose.template.yml
│   │   └── .dockerignore
│   ├── config/
│   │   ├── base_config.yaml         # Configuración base
│   │   └── agent_templates/         # Plantillas de configuración
│   ├── src/                         # 📦 Código compartido
│   │   ├── interfaces/              # Interfaces SOLID
│   │   ├── tools/                   # Herramientas comunes
│   │   └── utils/                   # Utilidades compartidas
│   └── scripts/
│       ├── create_agent.py          # 🚀 Script para crear nuevos agentes
│       └── deploy.sh                # Script de despliegue
├── agents/                          # 🤖 Agentes individuales
│   ├── base-agent/                  # Agente base
│   │   ├── config/
│   │   │   └── agent_config.yaml   # Solo configuración específica
│   │   ├── src/
│   │   │   └── tools/              # Herramientas específicas del agente
│   │   └── docker-compose.yml      # Hereda del template
│   ├── maritime-agent/              # Agente marítimo (ejemplo)
│   └── terrestrial-agent/          # Agente terrestre (ejemplo)
├── infrastructure/                  # 🏗️ Infraestructura compartida
│   ├── docker-compose.yml          # Orquestación completa
│   ├── nginx/                      # Proxy reverso
│   └── monitoring/                  # Monitoreo
├── agent-ui/                       # 🖥️ UI compartida
└── deploy.sh                       # 🚀 Script de despliegue principal
```

## 🚀 **Uso Rápido**

### **Desplegar Todo**
```bash
./deploy.sh deploy-all
```

### **Crear Nuevo Agente**
```bash
./deploy.sh create maritime-agent 8081 "Agente marítimo especializado"
```

### **Desplegar Agente Específico**
```bash
./deploy.sh deploy maritime-agent
```

### **Ver Estado**
```bash
./deploy.sh status
```

## 🔧 **Componentes Compartidos**

### **1. Dockerfile Base**
- ✅ Imagen base reutilizable
- ✅ Dependencias comunes
- ✅ Configuración estándar
- ✅ Variables de entorno consistentes

### **2. Interfaces SOLID**
- ✅ `IAgentService`: Servicio del agente
- ✅ `IAgentConfig`: Configuración del agente
- ✅ `ITool`: Herramientas del agente
- ✅ `IConfigLoader`: Cargador de configuración

### **3. Herramientas Comunes**
- ✅ `TimeTool`: Fecha y hora
- ✅ `MathTool`: Cálculos matemáticos
- ✅ `InfoTool`: Información del agente

### **4. Configuración Base**
- ✅ Modelos Gemini estándar
- ✅ Configuración de generación
- ✅ Logging consistente
- ✅ API endpoints estándar

## 🎯 **Beneficios de esta Arquitectura**

### **🔄 DRY (Don't Repeat Yourself)**
- ✅ Un solo Dockerfile base para todos los agentes
- ✅ Componentes compartidos reutilizables
- ✅ Configuración base común
- ✅ Scripts de despliegue unificados

### **📦 SRP (Single Responsibility)**
- ✅ Cada agente tiene una responsabilidad específica
- ✅ Componentes compartidos con responsabilidades claras
- ✅ Separación clara entre infraestructura y lógica de negocio

### **🔧 OCP (Open/Closed)**
- ✅ Nuevos agentes se crean sin modificar código existente
- ✅ Nuevas herramientas se pueden agregar fácilmente
- ✅ Configuración extensible sin cambios en código

### **🔗 LSP (Liskov Substitution)**
- ✅ Todos los agentes implementan las mismas interfaces
- ✅ Intercambiabilidad entre agentes
- ✅ Comportamiento consistente

### **🎯 ISP (Interface Segregation)**
- ✅ Interfaces específicas y cohesivas
- ✅ No hay dependencias innecesarias
- ✅ Facilita testing y mantenimiento

### **⬆️ DIP (Dependency Inversion)**
- ✅ Dependencias de abstracciones, no implementaciones
- ✅ Inyección de dependencias
- ✅ Facilita testing y mocking

## 🛠️ **Crear Nuevo Agente**

### **Paso 1: Crear Agente**
```bash
./deploy.sh create maritime-agent 8081 "Agente marítimo especializado"
```

### **Paso 2: Personalizar**
```bash
cd agents/maritime-agent
# Editar config/agent_config.yaml
# Agregar herramientas específicas en src/tools/
```

### **Paso 3: Desplegar**
```bash
./deploy.sh deploy maritime-agent
```

## 📊 **Monitoreo y Logging**

### **Logs Centralizados**
- ✅ Formato consistente en todos los agentes
- ✅ Niveles de logging configurables
- ✅ Timestamps y contexto

### **Métricas de Rendimiento**
- ✅ Tiempo de procesamiento
- ✅ Uso de tokens
- ✅ Herramientas utilizadas
- ✅ Estado de salud

## 🔒 **Seguridad**

### **Credenciales Centralizadas**
- ✅ Un solo punto de gestión de credenciales
- ✅ Montaje de solo lectura en contenedores
- ✅ No exposición en imágenes Docker

### **Redes Aisladas**
- ✅ Red Docker dedicada
- ✅ Comunicación controlada entre servicios
- ✅ Aislamiento de agentes

## 🚀 **Escalabilidad**

### **Horizontal**
- ✅ Múltiples instancias de agentes
- ✅ Load balancing automático
- ✅ Despliegue independiente

### **Vertical**
- ✅ Recursos configurables por agente
- ✅ Optimización específica por tipo de agente
- ✅ Monitoreo granular

## 📈 **Roadmap**

### **Fase 1: Base** ✅
- ✅ Arquitectura SOLID/DRY
- ✅ Agente base funcional
- ✅ UI compartida
- ✅ Scripts de despliegue

### **Fase 2: Especialización** 🚧
- 🚧 Agentes especializados (marítimo, terrestre)
- 🚧 Herramientas específicas por dominio
- 🚧 Configuraciones optimizadas

### **Fase 3: Orquestación** 📋
- 📋 API Gateway
- 📋 Load balancing
- 📋 Service discovery
- 📋 Health checks

### **Fase 4: Avanzado** 📋
- 📋 RAG (Retrieval Augmented Generation)
- 📋 Memoria persistente
- 📋 Aprendizaje continuo
- 📋 Análisis predictivo

---

**Esta arquitectura garantiza escalabilidad, mantenibilidad y adherencia a principios de desarrollo sólidos.**