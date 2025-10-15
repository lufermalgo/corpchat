# Model Selector Implementation - CorpChat

**Última actualización**: 15 Octubre 2025

---

## 🎯 Objetivo

Permitir a los usuarios seleccionar diferentes modelos LLM desde Open WebUI, similar a como ChatGPT presenta diferentes "thinking modes". Cada modelo tiene características específicas de pensamiento, temperatura y configuración.

---

## 🏗️ Arquitectura

### **Flujo de Usuario**
```
Usuario (Open WebUI) → Selector de Modelos → Gateway → Vertex AI Gemini
                    ↓
            Thinking Mode Aplicado → Respuesta Personalizada
```

### **Componentes Implementados**

1. **`model_selector.py`** - Configuración de modelos y thinking modes
2. **`app.py` (modificado)** - Gateway con soporte dinámico de modelos
3. **`test_model_selector.py`** - Tests E2E para validar funcionalidad

---

## 🤖 Modelos Disponibles

### **Modelos Rápidos (Instant)**
| Modelo OpenAI | Display Name | Thinking Mode | Temperature | Max Tokens | Descripción |
|---------------|--------------|---------------|-------------|------------|-------------|
| `gpt-4o-mini` | CorpChat Instant | Instant | 0.3 | 1024 | Respuestas rápidas |
| `gpt-3.5-turbo` | CorpChat Basic | Instant | 0.7 | 1024 | Modelo básico |

### **Modelos Balanceados (Thinking Mini)**
| Modelo OpenAI | Display Name | Thinking Mode | Temperature | Max Tokens | Descripción |
|---------------|--------------|---------------|-------------|------------|-------------|
| `gpt-4o` | CorpChat Standard | Thinking Mini | 0.7 | 2048 | Balance velocidad/calidad |

### **Modelos Profundos (Thinking)**
| Modelo OpenAI | Display Name | Thinking Mode | Temperature | Max Tokens | Descripción |
|---------------|--------------|---------------|-------------|------------|-------------|
| `gpt-4` | CorpChat Thinking | Thinking | 0.9 | 4096 | Análisis profundo |
| `gpt-4o-2024-07-18` | CorpChat Analyst | Thinking | 0.1 | 8192 | Análisis complejo |

### **Modelos Automáticos**
| Modelo OpenAI | Display Name | Thinking Mode | Temperature | Max Tokens | Descripción |
|---------------|--------------|---------------|-------------|------------|-------------|
| `gpt-4-turbo` | CorpChat Turbo | Auto | 0.5 | 8192 | Máxima velocidad + calidad |

---

## 🔧 Implementación Técnica

### **1. Configuración de Modelos (`model_selector.py`)**

```python
class ThinkingMode(Enum):
    AUTO = "auto"
    INSTANT = "instant"
    THINKING_MINI = "thinking_mini"
    THINKING = "thinking"

class ModelConfig:
    def __init__(self, vertex_model, display_name, description, 
                 thinking_mode, temperature=0.7, max_tokens=2048):
        self.vertex_model = vertex_model
        self.display_name = display_name
        self.description = description
        self.thinking_mode = thinking_mode
        self.temperature = temperature
        self.max_tokens = max_tokens
```

### **2. Endpoint de Modelos (`/v1/models`)**

```python
@app.get("/v1/models")
async def list_models():
    """Lista modelos disponibles para Open WebUI."""
    from model_selector import get_models_endpoint
    return get_models_endpoint()
```

**Respuesta**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o",
      "object": "model",
      "created": 1677610602,
      "owned_by": "corpchat",
      "display_name": "CorpChat Standard",
      "description": "Balance entre velocidad y calidad",
      "thinking_mode": "thinking_mini"
    }
  ]
}
```

### **3. Chat Completions Dinámico**

```python
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # Obtener configuración del modelo seleccionado
    model_config = get_model_config(request.model)
    
    # Aplicar thinking mode al mensaje
    enhanced_message = get_thinking_prompt(model_config, user_message)
    
    # Usar modelo específico de Vertex AI
    model = GenerativeModel(model_config.vertex_model)
```

### **4. Thinking Modes**

#### **Instant Mode**
```python
def get_thinking_prompt(model_config, user_message):
    if model_config.thinking_mode == ThinkingMode.INSTANT:
        return user_message  # Sin modificaciones
```

#### **Thinking Mini Mode**
```python
if model_config.thinking_mode == ThinkingMode.THINKING_MINI:
    return user_message + """
    
[INSTRUCCIÓN]: Piensa rápidamente pero de manera estructurada. 
Proporciona una respuesta directa y útil.
"""
```

#### **Thinking Mode**
```python
if model_config.thinking_mode == ThinkingMode.THINKING:
    return user_message + """
    
[INSTRUCCIÓN]: Piensa detenidamente sobre esta consulta. 
Considera múltiples perspectivas, analiza las implicaciones, 
y proporciona una respuesta completa y bien fundamentada. 
Si es relevante, incluye ejemplos o casos de uso.
"""
```

#### **Auto Mode**
```python
if model_config.thinking_mode == ThinkingMode.AUTO:
    return user_message + """
    
[INSTRUCCIÓN]: Determina automáticamente el nivel de 
análisis necesario para esta consulta. Si es simple, responde 
directamente. Si es compleja, toma tiempo para analizarla a fondo.
"""
```

---

## 🧪 Testing

### **Test E2E Completo**

```bash
# Ejecutar tests
python3 tests/e2e/test_model_selector.py
```

**Tests Incluidos**:
1. ✅ Endpoint `/v1/models` retorna modelos correctos
2. ✅ Diferentes modelos producen respuestas distintas
3. ✅ Thinking modes afectan la calidad/respuesta
4. ✅ Streaming funciona con todos los modelos

### **Verificación Manual**

```bash
# 1. Listar modelos disponibles
curl -X GET "https://gateway-url/v1/models"

# 2. Probar modelo instant
curl -X POST "https://gateway-url/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "¿Qué es CorpChat?"}]
  }'

# 3. Probar modelo thinking
curl -X POST "https://gateway-url/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "¿Qué es CorpChat?"}]
  }'
```

---

## 🚀 Deployment

### **1. Actualizar Gateway**

```bash
# Build y deploy
cd services/gateway
gcloud builds submit --config=cloudbuild.yaml --project=genai-385616
```

### **2. Verificar Deployment**

```bash
# Health check
curl -X GET "https://gateway-url/health"

# Models endpoint
curl -X GET "https://gateway-url/v1/models"
```

### **3. Configurar Open WebUI**

En Open WebUI, agregar el Gateway como proveedor:
- **URL**: `https://gateway-url/v1`
- **API Key**: (opcional, usando IAP)
- **Modelos**: Se detectarán automáticamente

---

## 💰 Costos y Performance

### **Costos por Modelo**
- **Todos usan**: `gemini-2.5-flash-001` (mismo costo base)
- **Costo**: ~$0.075/1M tokens input
- **Diferencia**: En tokens generados (thinking modes generan más)

### **Performance Esperada**
| Modelo | Tiempo Respuesta | Tokens Típicos | Calidad |
|--------|------------------|----------------|---------|
| Instant | 1-2s | 50-200 | Básica |
| Thinking Mini | 2-4s | 100-400 | Buena |
| Thinking | 3-6s | 200-800 | Excelente |
| Auto | 2-5s | Variable | Adaptativa |

---

## 🔮 Próximas Mejoras

### **Fase 1: Modelos Reales Diferentes**
- Usar `gemini-1.5-pro` para Thinking mode
- Usar `gemini-2.5-flash` para Instant mode
- Costos diferenciados por modelo

### **Fase 2: Configuración Avanzada**
- Temperature personalizable por usuario
- Max tokens configurable
- Modelos por rol (admin, user, guest)

### **Fase 3: Analytics**
- Tracking de uso por modelo
- Métricas de satisfacción por thinking mode
- Optimización automática de modelos

---

## 🎯 Resultado Final

### **Experiencia de Usuario**
1. **Usuario abre Open WebUI**
2. **Ve selector de modelos** (similar a ChatGPT)
3. **Selecciona modelo** según necesidad:
   - ⚡ **Instant**: Para consultas rápidas
   - 🧠 **Standard**: Para análisis balanceado
   - 🔬 **Thinking**: Para análisis profundo
   - 🤖 **Auto**: Para selección automática
4. **Recibe respuesta** optimizada para el modelo seleccionado

### **Beneficios**
- ✅ **Flexibilidad**: Usuario elige nivel de análisis
- ✅ **Transparencia**: Cada modelo tiene descripción clara
- ✅ **Performance**: Optimización por caso de uso
- ✅ **Escalabilidad**: Fácil agregar nuevos modelos
- ✅ **Compatibilidad**: 100% compatible con OpenAI API

---

**Estado**: 🟢 **IMPLEMENTADO Y LISTO PARA TESTING**  
**Complejidad**: Media (2-3 horas de implementación)  
**Impacto**: Alto (mejora significativa UX)

