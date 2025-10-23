# Configuración de Autenticación Google OIDC

## Variables de Entorno Requeridas

Para habilitar la autenticación Google OIDC en Open WebUI, necesitas configurar las siguientes variables de entorno en tu archivo `.env`:

```bash
# ----------------------------------------------------
# -- Project Naming Configuration
# ----------------------------------------------------
PROJECT_PREFIX=mychat

# ----------------------------------------------------
# -- GCP Configuration
# ----------------------------------------------------
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account-local.json

# ----------------------------------------------------
# -- Open WebUI Configuration
# ----------------------------------------------------
# This must point to the internal Docker network address of the gateway service.
# IMPORTANT: The hostname (mychat-gateway) must match your PROJECT_PREFIX.
OPENAI_API_BASE_URL=http://mychat-gateway:8080/v1

# Enable Google OIDC authentication.
OAUTH_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
OAUTH_CLIENT_SECRET=your-google-client-secret
OPENID_PROVIDER_URL=https://accounts.google.com
OAUTH_SCOPES=openid email profile
OAUTH_USERNAME_CLAIM=email
ENABLE_OAUTH_SIGNUP=true
ENABLE_OAUTH_PERSISTENT_CONFIG=false

# URL that the UI is publicly accessible from.
WEBUI_URL=http://localhost:3000

# Secret key for signing sessions. Generate a random one for production.
SECRET_KEY=your-random-secret-key-for-webui
```

## Configuración en Google Cloud Console

1. **Crear un proyecto OAuth 2.0:**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Navega a "APIs y servicios" > "Credenciales"
   - Haz clic en "Crear credenciales" > "ID de cliente OAuth 2.0"

2. **Configurar el tipo de aplicación:**
   - Selecciona "Aplicación web"
   - Nombre: "CorpChat Open WebUI"

3. **Configurar URIs autorizados:**
   - **Orígenes JavaScript autorizados:** `http://localhost:3000`
   - **URIs de redirección autorizados:** `http://localhost:3000/auth/oidc/callback`

4. **Obtener credenciales:**
   - Copia el `Client ID` y `Client Secret`
   - Actualiza las variables `OAUTH_CLIENT_ID` y `OAUTH_CLIENT_SECRET` en tu `.env`

## Verificación

Una vez configurado, reinicia los contenedores:

```bash
docker-compose down
docker-compose up -d
```

Accede a `http://localhost:3000` y deberías ver la opción de "Iniciar sesión con Google".
