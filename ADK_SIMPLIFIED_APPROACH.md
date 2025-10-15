# 🔄 ADK Simplified Approach - Decisión Técnica

**Fecha**: 2025-10-15  
**Estado**: Iteraciones con Runner/SessionService llegaron a un bloqueo

---

## ⚠️ **Problema Encontrado**

Después de múltiples iteraciones con la API de `Runner` y `Session`:

1. ✅ Session estructura correcta: `Session(id, appName, userId)`
2. ❌ `SessionService` no existe en `google.adk.sessions`
3. ❌ Documentación incompleta sobre cómo inicializar `session_service`
4. ⏱️ Ya llevamos ~12 deployments iterando en la API

**Error Actual**:
```
ImportError: cannot import name 'SessionService' from 'google.adk.sessions'
```

---

## 💡 **Alternativa Propuesta**

Según la documentación y ejemplos de ADK, los agentes pueden invocarse directamente sin usar `Runner`:

```python
# En lugar de:
runner = Runner(session_service=???)
async for event in runner.run_async(agent=orchestrator, ...):
    ...

# Usar directamente:
response = await orchestrator.run(message=request.message)
```

O con el pattern asíncrono:
```python
async for response in orchestrator.run_async(message=request.message):
    # Procesar response
```

---

## ✅ **Ventajas de la Alternativa**

1. **Simplicidad**: Menos componentes para configurar
2. **Documentación más clara**: Uso directo de agentes está mejor documentado
3. **MVP más rápido**: Podemos tener un MVP funcional hoy
4. **Iteración posterior**: Si necesitamos Runner + SessionService podemos agregarlo después

---

## 🎯 **Próxima Implementación**

Voy a simplificar `main.py` para invocar directamente el agente:

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    orchestrator = get_orchestrator()
    
    # Invocación directa del agente
    response = await orchestrator.run(
        message=request.message,
        # Cualquier contexto adicional necesario
    )
    
    # Guardar en Firestore
    firestore_client.add_message(...)
    
    return ChatResponse(response=response.text, ...)
```

---

**¿Estás de acuerdo con este enfoque más simple para el MVP?** 🚀

Podemos iterar y agregar `Runner` + `SessionService` después cuando tengamos más claridad de la API.

