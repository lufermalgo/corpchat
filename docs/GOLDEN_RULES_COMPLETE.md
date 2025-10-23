# 🔑 REGLAS DE ORO COMPLETAS - CORPCHAT

Este documento recopila todas las reglas de oro establecidas para el desarrollo del proyecto CorpChat.

## 1. 🏠 DESARROLLO LOCAL PRIMERO

### **Regla de Oro #1: Desarrollo Local Obligatorio**
- **TODO** el desarrollo debe hacerse en Docker Desktop local antes de pasar a Cloud Run
- Solo después de validar y probar localmente, se despliega a Cloud Run
- Esto garantiza estabilidad y reduce errores en producción

### **Regla de Oro #2: Verificación de Prerequisitos**
- Comprobar que la máquina tenga todos los prerequisitos listos para desarrollar
- Incluir verificación de Docker, Python, gcloud CLI, etc.
- Documentar cualquier dependencia adicional necesaria

### **Regla de Oro #3: Entorno Virtual Python**
- Usar **venv** de Python para instalación de paquetes
- Nunca instalar paquetes globalmente
- Mantener `requirements.txt` actualizados

### **Regla de Oro #4: Namespace Unificado**
- Agrupar todos los Docker en el mismo namespace
- Usar nombres consistentes: `corpchat-*`
- Facilitar gestión y limpieza de contenedores

## 2. 🔐 AUTENTICACIÓN Y SEGURIDAD

### **Regla de Oro #5: Autenticación Google Local**
- Solucionar la autenticación integrada de Google para desarrollo local
- Usar Application Default Credentials (ADC) cuando sea posible
- Mantener credenciales seguras y no hardcodear

### **Regla de Oro #6: No Hardcoding**
- Eliminar todo el hardcoding de variables críticas (endpoints, secrets, project IDs)
- Usar variables de entorno para multi-client replicability
- Validar que no haya valores hardcodeados en el código

## 3. 🚀 DEPLOYMENT Y VALIDACIÓN

### **Regla de Oro #7: Validación Post-Deployment**
- Después de cada deployment mensual, validar que todas las Cloud Run services estén habilitadas
- Verificar acceso correcto (interno o externo según requerimientos)
- Ejecutar scripts de validación automática

### **Regla de Oro #8: Verificación Completa de Servicios**
- Verificar que todos los servicios funcionen después de cada cambio
- No asumir que un servicio funciona sin validación
- Usar tests E2E para validar funcionalidad completa

## 4. 🧪 TESTING Y CALIDAD

### **Regla de Oro #9: Testing Real Obligatorio**
- Testing real obligatorio para cada componente antes de continuar
- Usar datos y acciones reales, nunca sintéticas o mockeadas
- Validar con flujos de usuario reales, APIs, bases de datos y servicios externos
- Las pruebas de latencia deben ser mediciones reales end-to-end

### **Regla de Oro #10: Máximo 2 Intentos**
- Cada requerimiento debe tener máximo 2 intentos de solución antes de consultar documentación
- Si no se resuelve en 2 intentos, revisar documentación oficial
- Evitar ciclos infinitos de corrección

## 5. 📚 DOCUMENTACIÓN Y ARQUITECTURA

### **Regla de Oro #11: Documentación Actualizada**
- Mantener PRD actualizado con todos los requerimientos funcionales y no funcionales
- Documentar todas las decisiones arquitectónicas
- Incluir guías de setup y deployment

### **Regla de Oro #12: Arquitectura Multi-Cliente**
- Diseñar para multi-client replicability desde el inicio
- Usar Infrastructure as Code (Terraform)
- Parametrizar todo lo necesario para diferentes clientes

## 6. 🔄 PROCESO DE DESARROLLO

### **Regla de Oro #13: Desarrollo Iterativo**
- Seguir metodología SCRUM con sprints definidos
- No pedir confirmación para mover entre sprints si las tareas están completas
- Mantener tracking en SCRUM_PLAN.md

### **Regla de Oro #14: Integración Continua**
- Usar Cloud Build para CI/CD
- Automatizar deployment y validación
- Mantener logs detallados de todos los procesos

## 7. 🎯 CALIDAD DE CÓDIGO

### **Regla de Oro #15: Estilo de Desarrollo**
- Seguir guía de estilo definida (PascalCase para clases, snake_case para funciones)
- Usar type hints de Python
- Implementar logging estructurado
- Manejo robusto de errores

### **Regla de Oro #16: Performance y Escalabilidad**
- Optimizar para performance desde el inicio
- Considerar escalabilidad en el diseño
- Monitorear métricas de rendimiento

## 8. 🌐 CONECTIVIDAD Y REDES

### **Regla de Oro #17: Conectividad Local**
- Asegurar que todos los servicios puedan comunicarse localmente
- Usar redes Docker apropiadas
- Configurar DNS interno si es necesario

### **Regla de Oro #18: Fallback y Resilencia**
- Implementar fallbacks para servicios externos
- Manejar desconexiones de red graciosamente
- Payload de respuesta consistente

---

## 9. 💬 COMUNICACIÓN Y FEEDBACK

### **Regla de Oro #19: Comunicación Directa y sin Filtros**
- El asistente de IA debe ser directo, conciso y evitar el lenguaje sicofante ("tienes razón", "excelente punto").
- Si una solicitud del usuario es incorrecta, ambigua o está planificada para una fase posterior, el asistente debe señalarlo claramente.
- El objetivo es un diálogo técnico y eficiente, no una conversación social.

## 10. 🤖 AUTONOMÍA Y DIRECTIVAS DEL ASISTENTE

### **Regla de Oro #20: Autonomía en Arquitectura y Decisiones Técnicas**
- El asistente de IA es totalmente autónomo para tomar las decisiones de arquitectura de software que mejor cumplan con los requerimientos del proyecto.
- Todas las decisiones se basarán en las mejores prácticas de la industria y los principios de un diseño robusto, escalable y mantenible.
- NUNCA presentar opciones al usuario para decisiones de arquitectura. El asistente debe tomar la mejor decisión directamente.

### **Regla de Oro #21: Autonomía en Ejecución y Validación**
- El asistente de IA es autónomo para ejecutar todos los comandos necesarios para el desarrollo, validación, revisión y despliegue del proyecto.
- Es responsabilidad del asistente verificar la salida de cada comando y garantizar que el sistema se encuentre en un estado funcional antes de notificar al usuario.

### **Regla de Oro #22: Comunicación Concisa**
- Las respuestas del asistente deben ser cortas y concretas, yendo directamente al punto para mantener un ritmo de desarrollo ágil y eficiente.

### **Regla de Oro #23: Adherencia a las Reglas de Oro**
- El asistente NUNCA DEBE OLVIDAR las reglas de oro. Son la directiva principal que gobierna todas sus acciones y respuestas.

## 📋 CHECKLIST DE CUMPLIMIENTO

Antes de cada deployment, verificar:

- [ ] Desarrollo completado y probado localmente
- [ ] Prerequisitos verificados
- [ ] Entorno virtual Python configurado
- [ ] Docker containers en namespace unificado
- [ ] Autenticación Google funcionando localmente
- [ ] No hay hardcoding en el código
- [ ] Tests E2E pasando
- [ ] Documentación actualizada
- [ ] Servicios validados y funcionando
- [ ] Acceso público configurado correctamente

## 🚨 VIOLACIONES DE REGLAS DE ORO

Si se detecta violación de alguna regla de oro:

1. **PARAR** el desarrollo inmediatamente
2. **CORREGIR** la violación antes de continuar
3. **DOCUMENTAR** la corrección
4. **ACTUALIZAR** procesos si es necesario

---

**Fecha de última actualización**: 2025-10-19
**Versión**: 2.0
**Autor**: CorpChat Development Team
