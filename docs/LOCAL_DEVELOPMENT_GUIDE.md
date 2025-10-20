# 🏠 Guía de Desarrollo Local para CorpChat

Esta guía te ayudará a configurar y ejecutar CorpChat en tu máquina local para desarrollo.

## 📋 Tabla de Contenidos

1. [Prerequisitos](#prerequisitos)
2. [Configuración Inicial](#configuración-inicial)
3. [Setup de Autenticación](#setup-de-autenticación)
4. [Configuración del Entorno](#configuración-del-entorno)
5. [Iniciar Desarrollo Local](#iniciar-desarrollo-local)
6. [Workflow de Desarrollo](#workflow-de-desarrollo)
7. [Testing y Validación](#testing-y-validación)
8. [Troubleshooting](#troubleshooting)
9. [Comandos Útiles](#comandos-útiles)

## 🔧 Prerequisitos

### Software Requerido

- **Python 3.12+**: Para el entorno virtual
- **Docker Desktop**: Para contenedores
- **Docker Compose**: Para orquestación
- **Google Cloud CLI**: Para autenticación
- **Git**: Para control de versiones

### Recursos del Sistema

- **RAM**: Mínimo 4GB, recomendado 8GB+
- **Espacio en disco**: Mínimo 10GB libres
- **Puertos disponibles**: 8080, 8081, 8082

### Verificación Automática

```bash
# Ejecutar verificación de prerequisitos
./scripts/check_prerequisites.sh
```

## 🚀 Configuración Inicial

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd CorpChat
```

### 2. Configurar Entorno Virtual

```bash
# Ejecutar setup automatizado
./scripts/setup_venv.sh

# O manualmente
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-local.txt
```

### 3. Configurar Git (si no está configurado)

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

## 🔐 Setup de Autenticación

### Opción 1: Service Account (Recomendado)

Sigue la guía detallada en [docs/LOCAL_AUTH_SETUP.md](LOCAL_AUTH_SETUP.md):

```bash
# 1. Crear Service Account
gcloud iam service-accounts create corpchat-local-dev

# 2. Asignar roles necesarios
gcloud projects add-iam-policy-binding genai-385616 \
    --member="serviceAccount:corpchat-local-dev@genai-385616.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# 3. Descargar credenciales
mkdir -p credentials
gcloud iam service-accounts keys create credentials/service-account-local.json \
    --iam-account=corpchat-local-dev@genai-385616.iam.gserviceaccount.com
```

### Opción 2: Application Default Credentials

```bash
# Autenticarse con gcloud
gcloud auth login
gcloud auth application-default login
gcloud config set project genai-385616
```

## ⚙️ Configuración del Entorno

### 1. Crear Archivo de Variables de Entorno

```bash
# Copiar template
cp env.local.template .env.local

# Editar configuración
nano .env.local  # o tu editor preferido
```

### 2. Variables Importantes a Configurar

```bash
# Autenticación Google
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account-local.json
GOOGLE_CLOUD_PROJECT=genai-385616
GOOGLE_CLOUD_LOCATION=us-central1

# Entorno
ENVIRONMENT=local

# Prefijos para evitar conflictos con producción
FIRESTORE_COLLECTION_PREFIX=corpchat_local
BIGQUERY_DATASET=corpchat_local
```

### 3. Verificar Configuración

```bash
# Test de autenticación
source .venv/bin/activate
python -c "
from google.cloud import firestore
client = firestore.Client(project='genai-385616')
print('✅ Autenticación Google OK')
"
```

## 🚀 Iniciar Desarrollo Local

### Método 1: Script Automatizado (Recomendado)

```bash
# Iniciar todos los servicios
./scripts/start_local.sh
```

Este script:
- ✅ Verifica prerequisitos
- ✅ Configura archivos necesarios
- ✅ Construye imágenes Docker
- ✅ Inicia servicios
- ✅ Verifica salud de servicios
- ✅ Muestra información útil

### Método 2: Manual

```bash
# 1. Verificar prerequisitos
./scripts/check_prerequisites.sh

# 2. Construir imágenes
docker-compose build

# 3. Iniciar servicios
docker-compose up -d

# 4. Verificar salud
docker-compose ps
curl http://localhost:8080/health
```

### Servicios Disponibles

Una vez iniciados, tendrás acceso a:

- **🚪 Gateway**: http://localhost:8080
- **📄 Ingestor**: http://localhost:8081  
- **🖥️ UI (Open WebUI)**: http://localhost:8082

## 💻 Workflow de Desarrollo

### Estructura de Desarrollo

```
CorpChat/
├── services/
│   ├── gateway/          # API Gateway
│   ├── ingestor/         # Document Processing
│   ├── ui/              # Open WebUI
│   └── agents/          # ADK Agents
├── scripts/             # Scripts de gestión
├── docs/               # Documentación
├── docker-compose.yml  # Orquestación local
└── .env.local          # Variables de entorno
```

### Hot Reload

Los archivos fuente están montados como volúmenes Docker, por lo que:

- ✅ Cambios en código se reflejan automáticamente
- ✅ No necesitas reconstruir imágenes para cambios de código
- ✅ Solo necesitas reconstruir para cambios en Dockerfile o requirements

### Flujo de Desarrollo Típico

1. **Hacer cambios en el código**
2. **Los cambios se reflejan automáticamente** (hot reload)
3. **Probar cambios** usando la UI o APIs
4. **Ejecutar tests** si es necesario
5. **Commit y push** cuando esté listo

### Comandos de Desarrollo

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f corpchat-gateway

# Reiniciar un servicio
docker-compose restart corpchat-gateway

# Ejecutar comandos en un contenedor
docker-compose exec corpchat-gateway bash

# Ver estado de servicios
docker-compose ps
```

## 🧪 Testing y Validación

### Tests Automatizados

```bash
# Ejecutar tests E2E completos
./scripts/test_local.sh
```

Los tests verifican:
- ✅ Conectividad básica
- ✅ Endpoints de APIs
- ✅ Funcionalidad de chat
- ✅ Speech-to-Text
- ✅ Procesamiento de documentos
- ✅ Memoria de conversaciones

### Tests Manuales

```bash
# Test de chat
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash-001",
    "messages": [{"role": "user", "content": "Hola"}]
  }'

# Test de modelos
curl http://localhost:8080/v1/models

# Test de health
curl http://localhost:8080/health
```

### Validación de UI

1. Abrir http://localhost:8082
2. Iniciar sesión con Google OAuth
3. Verificar que los modelos aparecen
4. Probar chat básico
5. Probar carga de archivos
6. Probar dictado (STT)

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Servicios no inician

```bash
# Verificar logs
docker-compose logs

# Verificar puertos ocupados
lsof -i :8080
lsof -i :8081
lsof -i :8082

# Limpiar y reiniciar
docker-compose down
docker-compose up -d
```

#### 2. Error de autenticación

```bash
# Verificar credenciales
ls -la credentials/

# Verificar variable de entorno
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test de autenticación
gcloud auth list
gcloud config get-value project
```

#### 3. UI no carga

```bash
# Verificar que UI está corriendo
docker-compose ps corpchat-ui

# Ver logs de UI
docker-compose logs corpchat-ui

# Verificar conectividad
curl http://localhost:8082/health
```

#### 4. Gateway no responde

```bash
# Verificar logs del Gateway
docker-compose logs corpchat-gateway

# Verificar conectividad interna
docker-compose exec corpchat-gateway curl http://localhost:8080/health

# Verificar variables de entorno
docker-compose exec corpchat-gateway env | grep GOOGLE
```

### Logs Útiles

```bash
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f corpchat-gateway

# Últimas 50 líneas
docker-compose logs --tail=50 corpchat-gateway

# Con timestamps
docker-compose logs -f -t corpchat-gateway
```

### Limpieza y Reset

```bash
# Detener servicios
./scripts/stop_local.sh

# Limpieza completa
docker-compose down -v --remove-orphans
docker system prune -f

# Reconstruir desde cero
docker-compose build --no-cache
docker-compose up -d
```

## 📚 Comandos Útiles

### Gestión de Servicios

```bash
# Iniciar desarrollo
./scripts/start_local.sh

# Detener desarrollo
./scripts/stop_local.sh

# Ejecutar tests
./scripts/test_local.sh

# Verificar prerequisitos
./scripts/check_prerequisites.sh
```

### Docker Compose

```bash
# Ver estado
docker-compose ps

# Ver logs
docker-compose logs -f

# Reiniciar servicios
docker-compose restart

# Reconstruir imágenes
docker-compose build

# Limpiar volúmenes
docker-compose down -v
```

### Desarrollo

```bash
# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements-local.txt

# Ejecutar tests Python
python -m pytest tests/

# Formatear código
black services/
flake8 services/
```

### Debugging

```bash
# Entrar a contenedor
docker-compose exec corpchat-gateway bash

# Ver variables de entorno
docker-compose exec corpchat-gateway env

# Verificar conectividad interna
docker-compose exec corpchat-gateway curl http://corpchat-ingestor:8080/health

# Ver logs en tiempo real
docker-compose logs -f --tail=100
```

## 🔗 Enlaces Útiles

- **UI (Open WebUI)**: http://localhost:8082
- **Gateway API**: http://localhost:8080
- **Ingestor API**: http://localhost:8081
- **Health Checks**: 
  - Gateway: http://localhost:8080/health
  - Ingestor: http://localhost:8081/health
  - UI: http://localhost:8082/health

## 📖 Documentación Adicional

- [Setup de Autenticación](LOCAL_AUTH_SETUP.md)
- [Troubleshooting Local](TROUBLESHOOTING_LOCAL.md)
- [Reglas de Oro](GOLDEN_RULES_COMPLETE.md)
- [PRD Actualizado](PRD_UPDATED_V2.md)

## 🆘 Soporte

Si encuentras problemas:

1. **Revisar logs**: `docker-compose logs -f`
2. **Ejecutar tests**: `./scripts/test_local.sh`
3. **Verificar prerequisitos**: `./scripts/check_prerequisites.sh`
4. **Consultar troubleshooting**: [docs/TROUBLESHOOTING_LOCAL.md](TROUBLESHOOTING_LOCAL.md)
5. **Crear issue** en el repositorio

---

**Última actualización**: 2025-10-19  
**Versión**: 1.0
