# Capacidades Administrativas de Open WebUI - CorpChat

**Última actualización**: 15 Octubre 2025

---

## 🎛️ Consola Administrativa de Open WebUI

### **Acceso a la Consola Admin**
```
Usuario Admin → Icono de Usuario (esquina superior derecha) → "Panel de administración"
```

### **Secciones Principales del Admin Panel**
1. **User Management** - Gestión de usuarios y roles
2. **Connections** - Conexiones con backends (nuestro Gateway)
3. **Models** - Gestión de modelos y modelfiles
4. **Settings** - Configuraciones globales
5. **Tools** - Herramientas y funciones personalizadas

---

## 👥 Gestión de Usuarios y Permisos

### **Roles Disponibles**
- **Admin**: Acceso completo a todas las funcionalidades
- **User**: Acceso limitado según configuración del admin

### **Control de Visibilidad por Usuario**
```
Admin puede configurar:
✅ Qué modelos puede ver cada usuario
✅ Qué funcionalidades están habilitadas
✅ Límites de uso por usuario
✅ Configuraciones específicas por rol
```

### **Ejemplo de Configuración Corporativa**
```
┌─────────────────────────────────────┐
│ Configuración por Rol               │
├─────────────────────────────────────┤
│ 👨‍💼 Ejecutivos                     │
│   - Modelos: gemini-1.5-pro         │
│   - Funciones: Análisis, RAG        │
│   - Límites: Sin restricciones      │
│                                     │
│ 👨‍💻 Desarrolladores                 │
│   - Modelos: gemini-1.5-flash       │
│   - Funciones: Coding, RAG          │
│   - Límites: 1000 requests/día      │
│                                     │
│ 👥 Usuarios Generales               │
│   - Modelos: gemini-2.5-flash       │
│   - Funciones: Chat básico          │
│   - Límites: 100 requests/día       │
└─────────────────────────────────────┘
```

---

## 🤖 Gestión de Modelos (Workspace)

### **Configuración de Modelos por Admin**
```
Admin → Workspace → Models → Configurar cada modelo
```

### **Personalización de Modelfiles**
Para cada modelo, el admin puede configurar:

#### **1. Información Básica**
- **Nombre del modelo** (como aparece al usuario)
- **Descripción** (ayuda contextual)
- **Categoría** (Fast, Analysis, Coding, etc.)

#### **2. System Prompts**
```python
# Ejemplo: System prompt para gemini-1.5-pro
"""
Eres CorpChat, el asistente corporativo de [NOMBRE_EMPRESA].
Especializado en análisis profundo y razonamiento complejo.

INSTRUCCIONES:
- Proporciona análisis detallados y bien fundamentados
- Incluye evidencia y ejemplos concretos
- Considera múltiples perspectivas
- Mantén un tono profesional y corporativo

CONTEXTO EMPRESARIAL:
- Industria: [INDUSTRIA]
- Valores: [VALORES_CORPORATIVOS]
- Políticas: [POLÍTICAS_RELEVANTES]
"""
```

#### **3. Parámetros del Modelo**
```json
{
  "temperature": 0.1,
  "max_tokens": 8192,
  "top_p": 0.9,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

#### **4. Sugerencias de Prompts**
```python
# Prompts sugeridos que aparecen al usuario
suggested_prompts = [
    "Analiza este documento y extrae los puntos clave",
    "Genera un resumen ejecutivo de esta información",
    "Identifica riesgos y oportunidades en este análisis",
    "Crea un plan de acción basado en estos datos"
]
```

#### **5. Documentos RAG Específicos**
- **Documentos corporativos** por modelo
- **Políticas y procedimientos** específicos
- **Bases de conocimiento** especializadas

---

## 🛠️ Herramientas y Funciones Personalizadas

### **Integración con OpenAPI Servers**
```
Admin → Settings → Tools → Add Custom Tool
```

### **Ejemplos de Herramientas Corporativas**
```python
# Herramienta: Consulta de Base de Datos Interna
{
  "name": "corporate_database",
  "description": "Consulta la base de datos corporativa",
  "endpoint": "https://internal-api.company.com/query",
  "parameters": {
    "query": "string",
    "department": "string"
  }
}

# Herramienta: Generación de Reportes
{
  "name": "generate_report",
  "description": "Genera reportes corporativos",
  "endpoint": "https://reports-api.company.com/generate",
  "parameters": {
    "template": "string",
    "data": "object"
  }
}
```

---

## 📊 Embeddings y RAG Corporativo

### **Configuración de Embeddings**
```
Admin → Settings → Embeddings → Configure
```

### **Bases de Conocimiento por Departamento**
```
┌─────────────────────────────────────┐
│ Bases de Conocimiento Corporativas  │
├─────────────────────────────────────┤
│ 📋 Recursos Humanos                 │
│   - Políticas de empleo            │
│   - Procedimientos de RRHH         │
│   - Manuales de capacitación       │
│                                     │
│ 💼 Finanzas                         │
│   - Políticas contables            │
│   - Procedimientos de gastos       │
│   - Reportes financieros           │
│                                     │
│ 🔧 IT/Seguridad                     │
│   - Políticas de seguridad         │
│   - Procedimientos técnicos        │
│   - Documentación de sistemas      │
│                                     │
│ 📈 Operaciones                      │
│   - Manuales de procesos           │
│   - Procedimientos operativos      │
│   - Métricas y KPIs                │
└─────────────────────────────────────┘
```

### **RAG Personalizado por Modelo**
```python
# Configuración RAG para gemini-1.5-pro (Analysis)
rag_config = {
  "model": "gemini-1.5-pro",
  "documents": [
    "corporate_policies.pdf",
    "financial_procedures.pdf",
    "strategic_plans.pdf"
  ],
  "search_strategy": "semantic",
  "context_window": 4000,
  "similarity_threshold": 0.7
}
```

---

## 🎨 Personalización de Interfaz

### **Branding Corporativo**
```
Admin → Settings → Interface → Customize
- Logo de la empresa
- Colores corporativos
- Mensaje de bienvenida personalizado
- Footer con información de contacto
```

### **Configuración de Chat**
```python
# Configuraciones por defecto para usuarios
default_settings = {
  "welcome_message": "¡Bienvenido a CorpChat! Tu asistente corporativo inteligente.",
  "max_conversation_length": 50,
  "enable_file_upload": True,
  "enable_web_search": False,  # Controlado por admin
  "default_model": "gemini-2.5-flash",
  "show_model_selector": True
}
```

---

## 🔐 Seguridad y Control

### **Políticas de Uso**
```
Admin puede configurar:
✅ Límites de requests por usuario/rol
✅ Restricciones de horario de uso
✅ Filtros de contenido
✅ Logs de auditoría
✅ Políticas de retención de datos
```

### **Monitoreo y Analytics**
```
Admin → Analytics → Dashboard
- Uso por usuario/rol
- Modelos más utilizados
- Tiempo de respuesta
- Costos por departamento
- Satisfacción del usuario
```

---

## 🚀 Configuración para CorpChat

### **Paso 1: Configurar Conexión**
```
Admin → Settings → Connections → Add Connection
- Name: "CorpChat Gemini Gateway"
- API Base: "https://corpchat-gateway-url/v1"
- API Key: (opcional, usando IAP)
- Models: Auto-detect (nuestros 6 modelos)
```

### **Paso 2: Configurar Modelos**
```
Admin → Workspace → Models → Configure each Gemini model

Para cada modelo:
1. Editar modelfile con system prompts corporativos
2. Configurar parámetros optimizados
3. Asociar documentos RAG específicos
4. Definir sugerencias de prompts
```

### **Paso 3: Configurar Usuarios**
```
Admin → User Management → Create Roles
1. Definir roles corporativos
2. Asignar modelos por rol
3. Configurar límites de uso
4. Establecer políticas de acceso
```

### **Paso 4: Configurar Herramientas**
```
Admin → Tools → Add Custom Tools
1. Integrar APIs corporativas
2. Configurar herramientas de negocio
3. Establecer permisos por herramienta
```

---

## 📋 Ejemplo de Configuración Completa

### **Modelfile para gemini-1.5-pro (Analysis)**
```yaml
# Modelfile corporativo
template: |
  Eres CorpChat, el asistente corporativo de Acme Corp.
  Especializado en análisis profundo y razonamiento estratégico.

  CONTEXTO CORPORATIVO:
  - Industria: Tecnología
  - Valores: Innovación, Excelencia, Integridad
  - Misión: Transformar el futuro con tecnología

  INSTRUCCIONES:
  - Proporciona análisis detallados y fundamentados
  - Incluye evidencia y ejemplos concretos
  - Considera implicaciones estratégicas
  - Mantén confidencialidad de datos sensibles

  FORMATO DE RESPUESTAS:
  - Estructura clara con secciones
  - Puntos clave destacados
  - Recomendaciones accionables
  - Referencias a políticas corporativas

parameters:
  temperature: 0.1
  max_tokens: 8192
  top_p: 0.9

suggested_prompts:
  - "Analiza este documento y extrae insights estratégicos"
  - "Evalúa los riesgos y oportunidades de esta propuesta"
  - "Genera un resumen ejecutivo con recomendaciones"
  - "Identifica patrones y tendencias en estos datos"

documents:
  - corporate_policies.pdf
  - strategic_plans.pdf
  - financial_reports.pdf
```

### **Configuración de Rol: Ejecutivos**
```json
{
  "role_name": "ejecutivos",
  "permissions": {
    "models": ["gemini-1.5-pro", "gemini-1.5-pro-vision"],
    "tools": ["corporate_database", "generate_report"],
    "rag_documents": "all",
    "daily_limit": "unlimited",
    "features": ["file_upload", "web_search", "model_comparison"]
  },
  "restrictions": {
    "business_hours_only": false,
    "content_filter": "corporate",
    "audit_logging": true
  }
}
```

---

## 🎯 Beneficios para CorpChat

### **1. Control Total del Admin**
- Configuración granular por modelo
- Prompts corporativos específicos
- Herramientas de negocio integradas
- RAG con documentos corporativos

### **2. Experiencia Personalizada por Usuario**
- Modelos asignados por rol
- Límites y permisos específicos
- Interfaz con branding corporativo
- Funcionalidades habilitadas según necesidad

### **3. Seguridad Empresarial**
- Control de acceso granular
- Logs de auditoría completos
- Políticas de uso configurables
- Integración con sistemas corporativos

### **4. Escalabilidad**
- Gestión centralizada
- Configuración por departamento
- Herramientas personalizables
- Analytics y monitoreo

---

## 📊 Resumen de Capacidades

| Funcionalidad | Admin Control | Usuario Final |
|---------------|---------------|---------------|
| **Modelos** | ✅ Configurar todos | 👀 Solo los asignados |
| **Prompts** | ✅ System prompts corporativos | 👀 Sugerencias predefinidas |
| **Herramientas** | ✅ APIs corporativas | 👀 Solo las permitidas |
| **RAG** | ✅ Documentos corporativos | 👀 Acceso según rol |
| **Límites** | ✅ Por usuario/rol | 👀 Transparente |
| **Interfaz** | ✅ Branding corporativo | 👀 Personalizada |

---

**Estado**: 🟢 **COMPLETAMENTE COMPATIBLE CON NUESTRA IMPLEMENTACIÓN**

La consola administrativa de Open WebUI nos permite tener control total sobre la experiencia del usuario, configurando modelos, prompts, herramientas y permisos según las necesidades corporativas.
