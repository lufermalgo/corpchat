# 🔧 Troubleshooting para Desarrollo Local de CorpChat

Esta guía te ayudará a resolver problemas comunes durante el desarrollo local de CorpChat.

## 📋 Tabla de Contenidos

1. [Problemas de Inicio](#problemas-de-inicio)
2. [Problemas de Docker](#problemas-de-docker)
3. [Problemas de Autenticación](#problemas-de-autenticación)
4. [Problemas de Red](#problemas-de-red)
5. [Problemas de Servicios](#problemas-de-servicios)
6. [Problemas de UI](#problemas-de-ui)
7. [Problemas de APIs](#problemas-de-apis)
8. [Problemas de Performance](#problemas-de-performance)
9. [Comandos de Diagnóstico](#comandos-de-diagnóstico)

## 🚀 Problemas de Inicio

### Error: "Script not found"

```bash
❌ ./scripts/start_local.sh: No such file or directory
```

**Solución**:
```bash
# Verificar que estás en el directorio correcto
pwd
ls -la scripts/

# Hacer ejecutable
chmod +x scripts/start_local.sh
```

### Error: "Prerequisitos no cumplidos"

```bash
❌ PREREQUISITOS FALTANTES
```

**Solución**:
```bash
# Instalar Docker Desktop
# Instalar gcloud CLI
# Configurar Python 3.12+

# Verificar instalaciones
docker --version
gcloud --version
python3 --version
```

### Error: "Puertos ocupados"

```bash
⚠️ Puertos ocupados: 8080 8081 8082
```

**Solución**:
```bash
# Ver qué está usando los puertos
lsof -i :8080
lsof -i :8081
lsof -i :8082

# Detener procesos que usan los puertos
sudo kill -9 <PID>

# O usar puertos diferentes
# Editar docker-compose.yml
```

## 🐳 Problemas de Docker

### Error: "Docker daemon not running"

```bash
❌ Cannot connect to the Docker daemon
```

**Solución**:
```bash
# Iniciar Docker Desktop
# En macOS: Abrir Docker Desktop desde Applications
# En Linux: sudo systemctl start docker

# Verificar que Docker está corriendo
docker info
```

### Error: "Image build failed"

```bash
❌ Error construyendo imágenes
```

**Solución**:
```bash
# Limpiar cache de Docker
docker system prune -f

# Reconstruir sin cache
docker-compose build --no-cache

# Ver logs detallados
docker-compose build --progress=plain
```

### Error: "Container exits immediately"

```bash
❌ Container corpchat-gateway exited with code 1
```

**Solución**:
```bash
# Ver logs del contenedor
docker-compose logs corpchat-gateway

# Entrar al contenedor para debug
docker-compose run --rm corpchat-gateway bash

# Verificar variables de entorno
docker-compose exec corpchat-gateway env
```

### Error: "Volume mount failed"

```bash
❌ Error mounting volume
```

**Solución**:
```bash
# Verificar permisos de archivos
ls -la .env.local
ls -la credentials/

# Verificar que los archivos existen
test -f .env.local && echo "✅ .env.local exists" || echo "❌ .env.local missing"
test -d credentials && echo "✅ credentials exists" || echo "❌ credentials missing"

# Recrear archivos si es necesario
cp env.local.template .env.local
mkdir -p credentials
```

## 🔐 Problemas de Autenticación

### Error: "Could not automatically determine credentials"

```bash
❌ Could not automatically determine credentials
```

**Solución**:
```bash
# Verificar variable de entorno
echo $GOOGLE_APPLICATION_CREDENTIALS

# Verificar que el archivo existe
ls -la credentials/service-account-local.json

# Configurar variable de entorno
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials/service-account-local.json"

# O usar gcloud auth
gcloud auth application-default login
```

### Error: "Permission denied"

```bash
❌ Permission denied on project genai-385616
```

**Solución**:
```bash
# Verificar autenticación
gcloud auth list

# Verificar proyecto configurado
gcloud config get-value project

# Cambiar proyecto si es necesario
gcloud config set project genai-385616

# Verificar roles del Service Account
gcloud projects get-iam-policy genai-385616 \
    --flatten="bindings[].members" \
    --filter="bindings.members:corpchat-local-dev@genai-385616.iam.gserviceaccount.com"
```

### Error: "Service account key invalid"

```bash
❌ Invalid service account key
```

**Solución**:
```bash
# Regenerar credenciales
gcloud iam service-accounts keys create credentials/service-account-local.json \
    --iam-account=corpchat-local-dev@genai-385616.iam.gserviceaccount.com

# Verificar formato del JSON
cat credentials/service-account-local.json | jq .
```

## 🌐 Problemas de Red

### Error: "Connection refused"

```bash
❌ Connection refused to corpchat-gateway:8080
```

**Solución**:
```bash
# Verificar que el servicio está corriendo
docker-compose ps

# Verificar logs del servicio
docker-compose logs corpchat-gateway

# Verificar conectividad interna
docker-compose exec corpchat-ingestor curl http://corpchat-gateway:8080/health

# Reiniciar servicios
docker-compose restart
```

### Error: "DNS resolution failed"

```bash
❌ Name or service not known
```

**Solución**:
```bash
# Verificar red de Docker
docker network ls
docker network inspect corpchat-local

# Recrear red
docker-compose down
docker network prune
docker-compose up -d
```

### Error: "Port already in use"

```bash
❌ Port 8080 is already in use
```

**Solución**:
```bash
# Encontrar proceso usando el puerto
lsof -i :8080

# Detener proceso
sudo kill -9 <PID>

# O cambiar puerto en docker-compose.yml
# ports: ["8083:8080"]  # Cambiar 8080 por 8083
```

## 🔧 Problemas de Servicios

### Error: "Gateway not responding"

```bash
❌ Gateway no responde
```

**Solución**:
```bash
# Verificar logs del Gateway
docker-compose logs corpchat-gateway

# Verificar que está corriendo
docker-compose ps corpchat-gateway

# Verificar health endpoint
curl -v http://localhost:8080/health

# Reiniciar Gateway
docker-compose restart corpchat-gateway
```

### Error: "Ingestor not processing files"

```bash
❌ Ingestor no procesa archivos
```

**Solución**:
```bash
# Verificar logs del Ingestor
docker-compose logs corpchat-ingestor

# Test manual del endpoint
curl -X POST http://localhost:8081/process \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_document.txt"

# Verificar conectividad con BigQuery
docker-compose exec corpchat-ingestor python -c "
from google.cloud import bigquery
client = bigquery.Client()
print('BigQuery connection OK')
"
```

### Error: "UI not loading"

```bash
❌ UI no carga
```

**Solución**:
```bash
# Verificar logs de UI
docker-compose logs corpchat-ui

# Verificar que está corriendo
docker-compose ps corpchat-ui

# Verificar conectividad
curl http://localhost:8082/health

# Verificar variables de entorno
docker-compose exec corpchat-ui env | grep OPENAI
```

## 🖥️ Problemas de UI

### Error: "Models not showing"

```bash
❌ No se muestran modelos en la UI
```

**Solución**:
```bash
# Verificar configuración de modelos
docker-compose exec corpchat-ui env | grep OPENAI_API_MODELS

# Verificar conectividad con Gateway
curl http://localhost:8080/v1/models

# Reiniciar UI
docker-compose restart corpchat-ui
```

### Error: "Chat not working"

```bash
❌ Chat no funciona
```

**Solución**:
```bash
# Verificar logs del Gateway
docker-compose logs corpchat-gateway

# Test manual del chat
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gemini-2.5-flash-001", "messages": [{"role": "user", "content": "test"}]}'

# Verificar autenticación de Vertex AI
docker-compose exec corpchat-gateway python -c "
import vertexai
vertexai.init(project='genai-385616', location='us-central1')
print('Vertex AI OK')
"
```

### Error: "File upload not working"

```bash
❌ Carga de archivos no funciona
```

**Solución**:
```bash
# Verificar logs del Ingestor
docker-compose logs corpchat-ingestor

# Test manual de carga
curl -X POST http://localhost:8081/process \
  -F "file=@test_document.txt" \
  -F "user_id=test-user"

# Verificar conectividad con Cloud Storage
docker-compose exec corpchat-ingestor python -c "
from google.cloud import storage
client = storage.Client()
print('Cloud Storage OK')
"
```

## 🔌 Problemas de APIs

### Error: "404 Not Found"

```bash
❌ 404 Not Found
```

**Solución**:
```bash
# Verificar endpoint correcto
curl http://localhost:8080/health
curl http://localhost:8080/v1/models

# Verificar rutas en el código
grep -r "@app.get" services/gateway/app.py

# Verificar que el servicio está corriendo
docker-compose ps
```

### Error: "500 Internal Server Error"

```bash
❌ 500 Internal Server Error
```

**Solución**:
```bash
# Ver logs detallados
docker-compose logs corpchat-gateway

# Verificar variables de entorno
docker-compose exec corpchat-gateway env

# Verificar conectividad con servicios externos
docker-compose exec corpchat-gateway python -c "
from google.cloud import firestore
client = firestore.Client()
print('Firestore OK')
"
```

### Error: "Timeout"

```bash
❌ Request timeout
```

**Solución**:
```bash
# Aumentar timeout en docker-compose.yml
# environment:
#   - TIMEOUT_SECONDS=60

# Verificar recursos del sistema
docker stats

# Reiniciar servicios
docker-compose restart
```

## ⚡ Problemas de Performance

### Error: "Slow response"

```bash
⚠️ Respuestas lentas
```

**Solución**:
```bash
# Verificar recursos del sistema
docker stats

# Verificar logs de performance
docker-compose logs | grep -i "time\|duration\|slow"

# Ajustar configuración
# En docker-compose.yml:
# environment:
#   - WORKER_COUNT=2
#   - MAX_CONNECTIONS=100
```

### Error: "High memory usage"

```bash
⚠️ Alto uso de memoria
```

**Solución**:
```bash
# Verificar uso de memoria
docker stats

# Limitar memoria por contenedor
# En docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 1G

# Reiniciar servicios
docker-compose restart
```

## 🔍 Comandos de Diagnóstico

### Verificación General

```bash
# Estado general
docker-compose ps
docker stats

# Logs generales
docker-compose logs --tail=50

# Verificar salud
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
```

### Verificación de Servicios

```bash
# Gateway
docker-compose logs corpchat-gateway
curl http://localhost:8080/v1/models

# Ingestor
docker-compose logs corpchat-ingestor
curl http://localhost:8081/health

# UI
docker-compose logs corpchat-ui
curl http://localhost:8082/health
```

### Verificación de Red

```bash
# Redes Docker
docker network ls
docker network inspect corpchat-local

# Conectividad interna
docker-compose exec corpchat-gateway ping corpchat-ingestor
docker-compose exec corpchat-ingestor ping corpchat-gateway
```

### Verificación de Volúmenes

```bash
# Volúmenes
docker volume ls
docker volume inspect corpchat-ui-data

# Montajes
docker-compose exec corpchat-gateway ls -la /app/credentials/
docker-compose exec corpchat-gateway cat /app/.env.local
```

### Verificación de Variables de Entorno

```bash
# Variables en contenedores
docker-compose exec corpchat-gateway env | grep GOOGLE
docker-compose exec corpchat-ingestor env | grep GOOGLE
docker-compose exec corpchat-ui env | grep OPENAI
```

## 🛠️ Soluciones de Emergencia

### Reset Completo

```bash
# Detener todo
docker-compose down -v --remove-orphans

# Limpiar Docker
docker system prune -a -f

# Limpiar archivos temporales
rm -f .env.local
rm -rf credentials/

# Reconfigurar
cp env.local.template .env.local
mkdir -p credentials
# Configurar credenciales...

# Reconstruir y reiniciar
docker-compose build --no-cache
docker-compose up -d
```

### Debugging Avanzado

```bash
# Entrar a contenedor
docker-compose exec corpchat-gateway bash

# Verificar procesos
docker-compose exec corpchat-gateway ps aux

# Verificar conectividad
docker-compose exec corpchat-gateway netstat -tulpn

# Verificar logs del sistema
docker-compose exec corpchat-gateway tail -f /var/log/syslog
```

## 📞 Obtener Ayuda

Si los problemas persisten:

1. **Recopilar información**:
   ```bash
   ./scripts/test_local.sh > test_results.log 2>&1
   docker-compose logs > docker_logs.log 2>&1
   ```

2. **Verificar documentación**:
   - [Guía de Desarrollo Local](LOCAL_DEVELOPMENT_GUIDE.md)
   - [Setup de Autenticación](LOCAL_AUTH_SETUP.md)
   - [Reglas de Oro](GOLDEN_RULES_COMPLETE.md)

3. **Crear issue** con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs relevantes
   - Información del sistema

---

**Última actualización**: 2025-10-19  
**Versión**: 1.0
