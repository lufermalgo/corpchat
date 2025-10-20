# 📋 PRODUCT REQUIREMENTS DOCUMENT (PRD) - CORPCHAT V2.0

**Versión**: 2.0  
**Fecha**: 2025-10-19  
**Estado**: Actualizado con nuevas reglas de oro y enfoque de desarrollo local

## 🎯 VISIÓN DEL PRODUCTO

CorpChat es una plataforma conversacional de inteligencia artificial generativa empresarial que centraliza el uso de IA para organizaciones, proporcionando una experiencia similar a ChatGPT/Gemini pero con control total sobre el core tecnológico y capacidad de despliegue multi-cliente.

## 🏗️ ARQUITECTURA ACTUALIZADA

### **Enfoque de Desarrollo Local-First**

```
┌─────────────────────────────────────────────────────────────┐
│                    DESARROLLO LOCAL                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Gateway   │  │  Ingestor   │  │     UI      │        │
│  │  (FastAPI)  │  │ (Pipeline)  │  │(Open WebUI) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │               │               │                  │
│  ┌─────────────────────────────────────────────────────────┤
│  │              DOCKER DESKTOP LOCAL                       │
│  │           Namespace: corpchat-local                     │
│  └─────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  PRODUCCIÓN CLOUD RUN                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Gateway   │  │  Ingestor   │  │     UI      │        │
│  │ (Cloud Run) │  │ (Cloud Run) │  │ (Cloud Run) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🔑 REGLAS DE ORO APLICADAS

### **1. Desarrollo Local Primero**
- Todo desarrollo en Docker Desktop local antes de Cloud Run
- Validación completa local antes de deployment
- Namespace unificado: `corpchat-local`

### **2. Autenticación Google Local**
- Application Default Credentials (ADC) para desarrollo local
- Service Account keys para servicios
- Configuración de `GOOGLE_APPLICATION_CREDENTIALS`

### **3. Multi-Client Replicability**
- Variables de entorno para todos los endpoints
- Sin hardcoding de project IDs o URLs
- Terraform para Infrastructure as Code

## 📊 REQUERIMIENTOS FUNCIONALES

### **MVP - Funcionalidades Core**

#### **1. Autenticación y Usuarios**
- ✅ **Google OAuth 2.0** integrado
- ✅ **Roles de usuario** (Admin, User)
- ✅ **Gestión de sesiones** persistente

#### **2. Modelos de IA**
- ✅ **Selección dinámica** de modelos Gemini
- ✅ **Model Selector** inteligente basado en contexto
- ✅ **Configuración dinámica** desde frontend

#### **3. Conversaciones**
- ✅ **Streaming responses** con SSE
- ✅ **Memoria híbrida** (working + long-term)
- ✅ **Historial persistente** en Firestore

#### **4. Procesamiento de Documentos**
- ✅ **Pipeline completo** (PDF, Excel, Word, imágenes)
- ✅ **Embeddings** en BigQuery Vector Search
- ✅ **RAG** con contexto enriquecido

#### **5. Speech-to-Text (STT)**
- ✅ **Google Cloud Speech-to-Text** integrado
- ✅ **Alta calidad** con configuración optimizada
- ✅ **Soporte para audios largos** (hasta 10 minutos)
- ✅ **Acumulación de transcripciones**

### **Funcionalidades Avanzadas**

#### **6. Multi-Agent Orchestration**
- ✅ **ADK Integration** con agentes especialistas
- ✅ **Tools integration** (Knowledge Base, Docs, Sheets)
- ✅ **Workflow automation**

#### **7. FinOps y Monitoreo**
- ✅ **Billing tracking** automático
- ✅ **Logging estructurado** con labels
- ✅ **Métricas de consumo** por servicio

## 🚀 REQUERIMIENTOS NO FUNCIONALES

### **Performance**
- **Latencia**: < 2 segundos para respuestas cortas
- **Throughput**: 100+ usuarios concurrentes
- **Streaming**: < 500ms para primer token

### **Escalabilidad**
- **Horizontal scaling** en Cloud Run
- **Auto-scaling** basado en demanda
- **Multi-region** deployment ready

### **Seguridad**
- **Autenticación** obligatoria
- **Autorización** basada en roles
- **Encriptación** en tránsito y reposo

### **Disponibilidad**
- **99.9%** uptime objetivo
- **Health checks** automáticos
- **Fallback** mechanisms

## 🛠️ STACK TECNOLÓGICO

### **Backend**
- **Python 3.12+** con venv
- **FastAPI** para APIs
- **Google Cloud SDK** para servicios GCP
- **Vertex AI** para modelos Gemini
- **ADK** para multi-agent orchestration

### **Frontend**
- **Open WebUI** como base
- **React/Svelte** para customizaciones
- **WebSocket/SSE** para streaming

### **Infrastructure**
- **Docker Desktop** para desarrollo local
- **Cloud Run** para producción
- **Terraform** para IaC
- **Cloud Build** para CI/CD

### **Data & Storage**
- **Firestore** para conversaciones y metadata
- **BigQuery** para embeddings y analytics
- **Cloud Storage** para archivos
- **Pub/Sub** para messaging

## 📋 PLAN DE TRABAJO ACTUALIZADO

### **FASE 1: SETUP DE DESARROLLO LOCAL** ⏳
- [ ] Verificar prerequisitos de la máquina
- [ ] Configurar entorno virtual Python
- [ ] Setup Docker Desktop con namespace unificado
- [ ] Configurar autenticación Google local
- [ ] Crear docker-compose para desarrollo local
- [ ] Validar conectividad entre servicios locales

### **FASE 2: DESARROLLO Y TESTING LOCAL** ⏳
- [ ] Implementar nuevas funcionalidades localmente
- [ ] Testing E2E en ambiente local
- [ ] Validación de calidad de código
- [ ] Optimización de performance local
- [ ] Documentación de APIs locales

### **FASE 3: DEPLOYMENT A CLOUD RUN** ⏳
- [ ] Deployment solo después de validación local
- [ ] Validación post-deployment automática
- [ ] Verificación de acceso público
- [ ] Testing E2E en producción
- [ ] Monitoreo y alertas

### **FASE 4: OPTIMIZACIONES** ⏳
- [ ] Optimización de costos (FinOps)
- [ ] Mejoras de performance
- [ ] Escalabilidad y auto-scaling
- [ ] Security hardening
- [ ] Disaster recovery

## 🔧 CONFIGURACIÓN LOCAL

### **Prerequisitos**
```bash
# Verificar instalaciones
python --version  # 3.12+
docker --version  # 24.0+
gcloud --version  # 450.0+
```

### **Setup de Entorno**
```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar Google Cloud
gcloud auth application-default login
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

### **Docker Compose Local**
```yaml
version: '3.8'
services:
  corpchat-gateway:
    build: ./services/gateway
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_CLOUD_PROJECT=local-dev
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
    networks:
      - corpchat-local

  corpchat-ingestor:
    build: ./services/ingestor
    ports:
      - "8081:8080"
    networks:
      - corpchat-local

  corpchat-ui:
    build: ./services/ui
    ports:
      - "8082:8080"
    networks:
      - corpchat-local

networks:
  corpchat-local:
    driver: bridge
```

## 📊 MÉTRICAS DE ÉXITO

### **Técnicas**
- **Deployment time**: < 5 minutos
- **Test coverage**: > 80%
- **Error rate**: < 1%
- **Response time**: < 2 segundos

### **Negocio**
- **User adoption**: 50+ usuarios activos
- **Satisfaction**: > 4.5/5 rating
- **Cost efficiency**: < $100/mes por cliente
- **Multi-client**: 3+ clientes desplegados

## 🚨 CRITERIOS DE ACEPTACIÓN

### **Funcionales**
- [ ] Usuarios pueden autenticarse con Google
- [ ] Conversaciones funcionan con streaming
- [ ] Documentos se procesan correctamente
- [ ] STT funciona con alta calidad
- [ ] Memoria persiste entre sesiones

### **No Funcionales**
- [ ] Servicios responden en < 2 segundos
- [ ] 99.9% uptime en producción
- [ ] Cero hardcoding en código
- [ ] Tests E2E pasando
- [ ] Documentación actualizada

## 📚 DOCUMENTACIÓN RELACIONADA

- [Reglas de Oro Completas](docs/GOLDEN_RULES_COMPLETE.md)
- [Guía de Estilo de Desarrollo](docs/DEVELOPMENT_STYLE_GUIDE.md)
- [Setup de Desarrollo Local](docs/LOCAL_DEVELOPMENT_SETUP.md)
- [Deployment Golden Rules](docs/DEPLOYMENT_GOLDEN_RULES.md)
- [Environment Variables](docs/ENVIRONMENT_VARIABLES.md)

---

**Próximos pasos**: Implementar FASE 1 - Setup de Desarrollo Local siguiendo las nuevas reglas de oro establecidas.
