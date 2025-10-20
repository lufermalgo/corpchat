# Flujo Interno del Model Selector - CorpChat

**Última actualización**: 15 Octubre 2025

---

## 🔄 Flujo Completo: Usuario → Core → Vertex AI

### **1. Selección del Usuario**
```
Usuario en Open WebUI selecciona: "gemini-1.5-pro"
```

### **2. Request HTTP**
```json
POST /v1/chat/completions
{
  "model": "gemini-1.5-pro",
  "messages": [
    {"role": "user", "content": "Analiza este código Python"}
  ]
}
```

### **3. Gateway Processing (app.py)**

#### **3.1 Obtener Configuración del Modelo**
```python
# Línea 336: Obtener configuración del modelo seleccionado
model_config = get_model_config(request.model)
# Resultado: ModelConfig para gemini-1.5-pro
```

#### **3.2 Configuración Específica del Modelo**
```python
# model_config contiene:
{
  "gemini_model": "gemini-1.5-pro-001",        # Modelo real de Vertex AI
  "display_name": "Gemini 1.5 Pro",
  "capability": "analysis",                     # Capacidad específica
  "temperature": 0.1,                          # Temperatura baja para análisis
  "max_tokens": 8192,                         # Máximo de tokens
  "supports_thinking": True,                  # Soporta razonamiento
  "supports_images": True,                    # Soporta imágenes
  "supports_code": True                       # Soporta código
}
```

#### **3.3 Inicializar Modelo Específico**
```python
# Línea 353: Crear modelo con configuración específica
model = GenerativeModel(model_config.gemini_model)
# Resultado: Instancia de gemini-1.5-pro-001
```

### **4. Aplicar Capacidades Específicas**

#### **4.1 Modificar Prompt del Usuario**
```python
# Líneas 372-376: Aplicar capacidades al mensaje
if gemini_messages:
    last_message = gemini_messages[-1].parts[0].text
    enhanced_message = get_capability_prompt(model_config, last_message)
    gemini_messages[-1].parts[0].text = enhanced_message
```

#### **4.2 Prompt Modificado por Capacidad**
```python
# Para gemini-1.5-pro (ANALYSIS):
mensaje_original = "Analiza este código Python"

mensaje_mejorado = """Analiza este código Python

[INSTRUCCIÓN]: Realiza un análisis profundo y detallado. Considera múltiples 
perspectivas, proporciona evidencia y ejemplos concretos cuando sea apropiado."""
```

### **5. Configuración de Generación**
```python
# Líneas 378-382: Configuración específica del modelo
generation_config = {
    "temperature": 0.1,      # Baja para análisis preciso
    "max_output_tokens": 8192  # Alto para respuestas detalladas
}
```

### **6. Llamada a Vertex AI**
```python
# Línea 384: Iniciar chat con modelo específico
chat = model.start_chat()

# Líneas 386-395: Enviar mensajes y obtener respuesta
response = chat.send_message(
    enhanced_message,
    generation_config=generation_config
)
```

---

## 🎯 Diferencias por Modelo Seleccionado

### **Ejemplo 1: gemini-2.5-flash (FAST)**
```python
# Configuración
{
  "gemini_model": "gemini-2.5-flash-001",
  "temperature": 0.7,
  "max_tokens": 8192,
  "capability": "fast"
}

# Prompt modificado
mensaje_original = "¿Qué es Python?"
mensaje_mejorado = "¿Qué es Python?"  # Sin modificaciones
```

### **Ejemplo 2: gemini-1.5-flash (CODING)**
```python
# Configuración
{
  "gemini_model": "gemini-1.5-flash-001",
  "temperature": 0.3,
  "max_tokens": 8192,
  "capability": "coding"
}

# Prompt modificado
mensaje_original = "¿Cómo crear una función?"
mensaje_mejorado = """¿Cómo crear una función?

[INSTRUCCIÓN]: Eres un experto en programación. Si la consulta involucra código, 
proporciona ejemplos prácticos y mejores prácticas. Si no es sobre programación, 
responde normalmente."""
```

### **Ejemplo 3: gemini-1.5-pro-vision (IMAGE_GENERATION)**
```python
# Configuración
{
  "gemini_model": "gemini-1.5-pro-001",
  "temperature": 0.7,
  "max_tokens": 8192,
  "capability": "image_generation"
}

# Prompt modificado
mensaje_original = "Describe esta imagen"
mensaje_mejorado = """Describe esta imagen

[INSTRUCCIÓN]: Si la consulta involucra imágenes, análisis visual o generación 
de contenido visual, proporciona una respuesta detallada. Si no, responde normalmente."""
```

---

## 🔧 Logging y Monitoreo

### **Log Estructurado**
```python
# Líneas 338-350: Log detallado del modelo usado
_logger.info(
    f"Using Gemini model: {model_config.display_name} ({model_config.capability.value})",
    extra={
        "user_id": user_id,
        "selected_model": request.model,           # gemini-1.5-pro
        "gemini_model": model_config.gemini_model, # gemini-1.5-pro-001
        "capability": model_config.capability.value, # analysis
        "supports_thinking": model_config.supports_thinking, # True
        "supports_images": model_config.supports_images,     # True
        "supports_code": model_config.supports_code,         # True
        "labels": {"service": "gateway", "team": "corpchat"}
    }
)
```

---

## 🚀 Ventajas del Sistema

### **1. Flexibilidad**
- Usuario elige modelo según necesidad
- Cada modelo optimizado para tarea específica
- Configuraciones automáticas por modelo

### **2. Eficiencia**
- No desperdicia recursos en modelos pesados para tareas simples
- Usa modelo ligero para respuestas rápidas
- Usa modelo potente para análisis complejos

### **3. Experiencia de Usuario**
- Interfaz familiar (como ChatGPT)
- Selección intuitiva por capacidad
- Resultados optimizados por modelo

### **4. Escalabilidad**
- Fácil agregar nuevos modelos de Gemini
- Configuración centralizada
- Logging detallado para monitoreo

---

## 📊 Comparación de Modelos en Acción

### **Consulta: "Explica qué es Python"**

| Modelo Seleccionado | Modelo Real Usado | Prompt Aplicado | Resultado |
|---------------------|-------------------|-----------------|-----------|
| `gemini-2.5-flash` | gemini-2.5-flash-001 | Sin modificaciones | Respuesta rápida y directa |
| `gemini-1.5-pro` | gemini-1.5-pro-001 | + Análisis profundo | Respuesta detallada con ejemplos |
| `gemini-1.5-flash` | gemini-1.5-flash-001 | + Enfoque en código | Respuesta con ejemplos de código |

### **Consulta: "Analiza este algoritmo"**

| Modelo Seleccionado | Comportamiento |
|---------------------|----------------|
| `gemini-2.5-flash` | Explicación básica |
| `gemini-1.5-pro` | Análisis profundo con múltiples perspectivas |
| `gemini-1.5-flash` | Análisis con ejemplos de código |

---

## 🔍 Debugging y Troubleshooting

### **Verificar Modelo Usado**
```bash
# En logs de Cloud Run
gcloud logs read "resource.type=cloud_run_revision" \
  --project=genai-385616 \
  --filter="jsonPayload.labels.service=gateway" \
  --format="value(jsonPayload.gemini_model)"
```

### **Verificar Configuración Aplicada**
```bash
# Ver configuración específica del modelo
gcloud logs read "resource.type=cloud_run_revision" \
  --project=genai-385616 \
  --filter="jsonPayload.capability=analysis" \
  --format="value(jsonPayload.temperature,jsonPayload.max_tokens)"
```

---

## 🎯 Resumen del Flujo Interno

1. **Usuario selecciona modelo** → Open WebUI envía request
2. **Gateway recibe request** → Extrae modelo seleccionado
3. **get_model_config()** → Obtiene configuración específica
4. **GenerativeModel()** → Crea instancia del modelo real de Gemini
5. **get_capability_prompt()** → Modifica prompt según capacidad
6. **generation_config** → Aplica temperatura/tokens específicos
7. **Vertex AI** → Procesa con modelo y configuración específicos
8. **Respuesta optimizada** → Retorna resultado según capacidad del modelo

**Resultado**: Cada modelo produce respuestas diferentes, optimizadas para su capacidad específica, usando el modelo real de Gemini correspondiente.

