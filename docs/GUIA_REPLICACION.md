# Guía de Replicación CorpChat

## 🎯 Objetivo

Esta guía proporciona instrucciones paso a paso para replicar la plataforma CorpChat para nuevos clientes, manteniendo la modularidad y escalabilidad del sistema.

## 📋 Prerequisitos

### **Software Requerido**
- Docker Desktop 4.0+
- Docker Compose 2.0+
- Git
- Editor de texto (VS Code recomendado)

### **Cuentas y Credenciales**
- Google Cloud Platform (GCP) con proyecto activo
- Service Account con permisos de Vertex AI
- Google OAuth 2.0 Client ID y Secret

## 🚀 Proceso de Replicación

### **Paso 1: Preparación del Entorno**

```bash
# 1. Clonar el repositorio base
git clone <repository-url>
cd CorpChat

# 2. Crear directorio para el nuevo cliente
mkdir -p clients/<nombre-cliente>
cd clients/<nombre-cliente>

# 3. Copiar archivos base
cp -r ../../services .
cp -r ../../docs .
cp ../../docker-compose.yml .
cp ../../.env.example .env
```

### **Paso 2: Configuración del Cliente**

#### **2.1 Variables de Entorno**
Editar `.env` con valores específicos del cliente:

```bash
# Identificación única del cliente
PROJECT_PREFIX=<nombre-cliente>

# Google Cloud Platform
GCP_PROJECT_ID=<proyecto-gcp-cliente>
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account-local.json

# Google OIDC (crear en Google Cloud Console)
GOOGLE_CLIENT_ID=<client-id-cliente>
GOOGLE_CLIENT_SECRET=<client-secret-cliente>

# Seguridad
SECRET_KEY=<secret-key-unico-cliente>
```

#### **2.2 Service Account**
```bash
# Crear directorio de credenciales
mkdir -p credentials

# Copiar service account JSON del cliente
cp <path-to-service-account.json> credentials/service-account-local.json
```

### **Paso 3: Configuración de Modelos**

Editar `services/backend/config/models.yaml`:

```yaml
models:
  <cliente>-fast:
    display_name: "<Cliente> Super Fast"
    description: "Respuestas ultra rápidas para <Cliente>"
    llm_model: "gemini-2.5-flash-lite"
    
  <cliente>-thinking:
    display_name: "<Cliente> Thinking"
    description: "Razonamiento avanzado para <Cliente>"
    llm_model: "gemini-2.5-pro"
    
  <cliente>-images:
    display_name: "<Cliente> Images"
    description: "Generación de imágenes para <Cliente>"
    llm_model: "gemini-2.5-flash-lite"
```

### **Paso 4: Configuración de Agentes**

Editar `services/backend/config/agents.yaml`:

```yaml
agents:
  orchestrator:
    name: "<cliente>_orchestrator"
    description: "Orchestrator para <Cliente>"
    # ... resto de configuración
    
  generalist:
    name: "<cliente>_generalist_agent"
    description: "Agente generalista para <Cliente>"
    # ... resto de configuración
```

### **Paso 5: Configuración de Prompts**

Editar `services/backend/config/prompts.yaml`:

```yaml
prompts:
  orchestrator:
    system: |
      Eres el orchestrator de <Cliente> que gestiona conversaciones
      y delega tareas a agentes especializados usando el protocolo A2A.
      # ... resto del prompt
      
  generalist:
    system: |
      Eres un agente generalista de <Cliente> que procesa solicitudes
      usando diferentes modelos de IA basados en la selección del usuario.
      # ... resto del prompt
```

### **Paso 6: Despliegue**

```bash
# 1. Construir y ejecutar servicios
docker-compose up --build -d

# 2. Verificar que todos los servicios estén ejecutándose
docker ps | grep <nombre-cliente>

# 3. Verificar logs
docker logs <nombre-cliente>-orchestrator
docker logs <nombre-cliente>-agent-generalist
docker logs <nombre-cliente>-gateway
docker logs <nombre-cliente>-ui
```

### **Paso 7: Validación**

#### **7.1 Pruebas de Conectividad**
```bash
# Probar endpoint de salud
curl http://localhost:8080/health

# Probar modelos disponibles
curl http://localhost:8080/v1/models
```

#### **7.2 Pruebas de Funcionalidad**
```bash
# Probar modelo rápido
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hola"}], "model": "<cliente>-fast"}'

# Probar modelo de razonamiento
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Explica la IA"}], "model": "<cliente>-thinking"}'
```

#### **7.3 Pruebas de UI**
```bash
# Abrir navegador
open http://localhost:3000

# Verificar autenticación Google
# Verificar selector de modelos
# Probar conversación
```

## 🔧 Personalización Avanzada

### **Configuración de Dominio Personalizado**

```bash
# En .env
WEBUI_URL=https://<dominio-cliente>.com
CORS_ALLOW_ORIGIN=https://<dominio-cliente>.com

# En docker-compose.yml
ports:
  - "443:8080"  # HTTPS
  - "80:8080"   # HTTP redirect
```

### **Configuración de Base de Datos**

```yaml
# Agregar a docker-compose.yml
services:
  database:
    image: postgres:15
    environment:
      POSTGRES_DB: <cliente>_corpchat
      POSTGRES_USER: <usuario>
      POSTGRES_PASSWORD: <password>
    volumes:
      - <cliente>_db_data:/var/lib/postgresql/data
    networks:
      - corpchat-net
```

### **Configuración de Monitoreo**

```yaml
# Agregar a docker-compose.yml
services:
  monitoring:
    image: prometheus/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - corpchat-net
```

## 🚨 Troubleshooting

### **Problemas Comunes**

#### **Error: "Cannot connect to host"**
```bash
# Verificar que todos los servicios estén en la misma red
docker network ls
docker network inspect <nombre-cliente>_corpchat-net
```

#### **Error: "Google OIDC authentication failed"**
```bash
# Verificar variables de entorno
docker exec <nombre-cliente>-ui env | grep GOOGLE

# Verificar configuración en Google Cloud Console
# - Redirect URIs: http://localhost:3000/auth/callback
# - Authorized domains: localhost
```

#### **Error: "Vertex AI permission denied"**
```bash
# Verificar service account
docker exec <nombre-cliente>-orchestrator cat /app/credentials/service-account-local.json

# Verificar permisos en GCP
# - Vertex AI User
# - AI Platform Developer
```

### **Logs de Debugging**

```bash
# Logs detallados de todos los servicios
docker-compose logs -f

# Logs específicos por servicio
docker logs <nombre-cliente>-orchestrator --tail 50
docker logs <nombre-cliente>-agent-generalist --tail 50
docker logs <nombre-cliente>-gateway --tail 50
docker logs <nombre-cliente>-ui --tail 50
```

## 📊 Checklist de Validación

### **Pre-Despliegue**
- [ ] Variables de entorno configuradas
- [ ] Service Account JSON válido
- [ ] Google OIDC configurado
- [ ] Configuración YAML personalizada
- [ ] Dominio/URLs configurados

### **Post-Despliegue**
- [ ] Todos los contenedores ejecutándose
- [ ] Endpoints de salud respondiendo
- [ ] Modelos disponibles en API
- [ ] UI accesible y funcional
- [ ] Autenticación Google funcionando
- [ ] Conversaciones funcionando
- [ ] A2A HTTP funcionando
- [ ] Logs sin errores críticos

### **Validación de Cliente**
- [ ] Respuestas personalizadas del cliente
- [ ] Branding/configuración específica
- [ ] Performance dentro de parámetros
- [ ] Seguridad implementada
- [ ] Documentación entregada

## 📚 Recursos Adicionales

- [Documentación de Arquitectura](./ARQUITECTURA_BASE_COMPLETA.md)
- [Configuración de Google OIDC](./GOOGLE_OAUTH_SETUP.md)
- [Reglas de Oro del Proyecto](./GOLDEN_RULES_COMPLETE.md)
- [Troubleshooting Avanzado](./TROUBLESHOOTING.md)

---

**Versión**: 1.0  
**Fecha**: 2025-10-23  
**Mantenido por**: CorpChat Development Team
