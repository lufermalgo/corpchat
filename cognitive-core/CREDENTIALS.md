# 🔐 Gestión de Credenciales - Cognitive Core

## 📍 Ubicación Centralizada

Las credenciales del proyecto están centralizadas en:
```
/Users/lufermalgo/Proyectos/CorpChat/credentials/
```

## 📁 Estructura de Credenciales

```
credentials/
└── service-account-local.json    # Service Account de Google Cloud
```

## 🔧 Configuración en Contenedores

### Docker Compose
Los contenedores montan las credenciales como volumen de solo lectura:

```yaml
volumes:
  - /Users/lufermalgo/Proyectos/CorpChat/credentials:/app/credentials:ro
```

### Variables de Entorno
```bash
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account-local.json
GOOGLE_CLOUD_PROJECT=genai-385616
GOOGLE_CLOUD_REGION=us-central1
```

## ✅ Beneficios de la Centralización

### 🔒 Seguridad
- Las credenciales no se incluyen en las imágenes Docker
- Acceso de solo lectura desde los contenedores
- Fácil rotación de credenciales sin reconstruir imágenes

### 🔄 Reutilización
- Múltiples agentes pueden usar las mismas credenciales
- Consistencia en la autenticación across el proyecto
- Un solo punto de gestión para todas las credenciales

### 🛠️ Mantenimiento
- Cambios de credenciales sin reconstruir contenedores
- Fácil backup y versionado de credenciales
- Gestión centralizada de permisos

## 🚀 Uso en Nuevos Agentes

Para agregar un nuevo agente que use las credenciales centralizadas:

1. **En el Dockerfile**: No copiar credenciales locales
2. **En docker-compose.yml**: Agregar el volumen de credenciales
3. **Variables de entorno**: Configurar `GOOGLE_APPLICATION_CREDENTIALS`

### Ejemplo de docker-compose.yml:
```yaml
services:
  nuevo-agente:
    build: .
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account-local.json
      - GOOGLE_CLOUD_PROJECT=genai-385616
      - GOOGLE_CLOUD_REGION=us-central1
    volumes:
      - /Users/lufermalgo/Proyectos/CorpChat/credentials:/app/credentials:ro
```

## 🔍 Verificación

Para verificar que las credenciales están montadas correctamente:

```bash
# Verificar que el archivo existe en el contenedor
docker exec <container_name> ls -la /app/credentials/

# Verificar que la variable de entorno está configurada
docker exec <container_name> env | grep GOOGLE_APPLICATION_CREDENTIALS
```

## 📝 Notas Importantes

- Las credenciales se montan como **solo lectura** (`:ro`)
- El path debe ser **absoluto** en el docker-compose.yml
- Las credenciales deben existir en el host antes de iniciar los contenedores
- Para desarrollo local, asegúrate de que el archivo `service-account-local.json` tenga los permisos correctos
