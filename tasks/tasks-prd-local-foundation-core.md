## Relevant Files

- `docker-compose.yml`
- `.env.example`
- `/config/orchestrator/settings.py`
- `/config/agent-generalist/settings.py`
- `/services/gateway/Dockerfile`
- `/services/gateway/nginx.conf`
- `/services/ui/Dockerfile`
- `/services/ui/branding/corpchat.css`
- `/services/backend/Dockerfile`
- `/services/backend/requirements.txt`
- `/services/backend/src/orchestrator.py`
- `/services/backend/src/agent_generalist.py`

## Tasks

- [ ] **1.0 Fundamentos y Estructura de Directorios (Modelo Canónico 2.0)**
  - [ ] 1.1 Crear la estructura de directorios: `/config/orchestrator`, `/config/agent-generalist`, `/services/gateway`, `/services/ui/branding`, `/services/backend/src`.
  - [ ] 1.2 Crear los ficheros `.env.example` y `.gitignore`.
  - [ ] 1.3 Definir `PROJECT_PREFIX` en `.env.example`.

- [ ] **2.0 Base Común del Backend**
  - [ ] 2.1 Crear `services/backend/Dockerfile` con una imagen base de Python.
  - [ ] 2.2 Crear `services/backend/requirements.txt` y añadir `google-adk`.
  - [ ] 2.3 Configurar el `Dockerfile` para instalar dependencias y copiar el código de `src`.

- [ ] **3.0 Servicio de Gateway (Nginx)**
  - [ ] 3.1 Crear `services/gateway/Dockerfile` usando la imagen `nginx`.
  - [ ] 3.2 Crear `services/gateway/nginx.conf` con la regla de `proxy_pass` hacia el servicio `orchestrator`.
  - [ ] 3.3 Configurar el `Dockerfile` para que copie el `nginx.conf`.

- [ ] **4.0 Servicio de UI (Open WebUI)**
  - [ ] 4.1 Crear `services/ui/Dockerfile` derivado de `open-webui`.
  - [ ] 4.2 Crear `services/ui/branding/corpchat.css` para el tema.
  - [ ] 4.3 Configurar el `Dockerfile` de la UI para que copie el `corpchat.css`.

- [ ] **5.0 Orquestación con Docker Compose**
  - [ ] 5.1 Crear `docker-compose.yml` y definir la red `${PROJECT_PREFIX}-net`.
  - [ ] 5.2 **Servicio `gateway`**:
    - [ ] 5.2.1 Configurar `build` (`services/gateway`), `container_name`, `ports` y `networks`.
  - [ ] 5.3 **Servicio `ui`**:
    - [ ] 5.3.1 Configurar `build` (`services/ui`), `container_name` y `networks`.
    - [ ] 5.3.2 Configurar variables de entorno (`OIDC_*`, `OPENAI_API_BASE_URL` apuntando a `http://gateway`, etc.).
  - [ ] 5.4 **Servicio `orchestrator`**:
    - [ ] 5.4.1 Configurar `build` (`services/backend`), `container_name` y `networks`.
    - [ ] 5.4.2 Especificar el `command` para `python src/orchestrator.py`.
    - [ ] 5.4.3 Montar volúmenes para `credentials` y para `config/orchestrator`.
  - [ ] 5.5 **Servicio `agent-generalist`**:
    - [ ] 5.5.1 Configurar `build` (`services/backend`), `container_name` y `networks`.
    - [ ] 5.5.2 Especificar el `command` para `python src/agent_generalist.py`.
    - [ ] 5.5.3 Montar volúmenes para `credentials` y para `config/agent-generalist`.

- [ ] **6.0 Implementación del Código ADK**
  - [ ] 6.1 Implementar el esqueleto del servidor ADK en `orchestrator.py` con su endpoint.
  - [ ] 6.2 Implementar el esqueleto del servidor ADK en `agent_generalist.py` con su endpoint A2A.
  - [ ] 6.3 Implementar la lógica de `FirestoreMemory` en el `orchestrator`.
  - [ ] 6.4 Implementar la llamada A2A desde el `orchestrator` al `agent-generalist`.
  - [ ] 6.5 Implementar la lógica de selección de API de Vertex en el `agent-generalist`.

- [ ] **7.0 Verificación y Finalización**
  - [ ] 7.1 Verificar el flujo E2E: Login -> Chat -> Respuesta.
  - [ ] 7.2 Confirmar en los logs que la comunicación sigue el patrón `UI -> Gateway -> Orchestrator -> Agent`.
  - [ ] 7.3 Documentar todas las variables de entorno en un `README.md`.

## FASE FUTURA: Sistema de Gestión de Agentes Especializados

**Problema Identificado**: La arquitectura actual no es escalable para agentes especializados reales. Se requiere un sistema completo de gestión de agentes.

### **8.0 Análisis y Diseño del Sistema de Agentes Especializados**
- [ ] 8.1 **Análisis de Requerimientos**:
  - [ ] 8.1.1 Definir qué constituye un "agente especializado" completo (tools, prompts, capabilities, etc.).
  - [ ] 8.1.2 Analizar cómo Open WebUI maneja la importación/exportación de modelos para replicar el patrón.
  - [ ] 8.1.3 Definir el formato estándar para "Agent Packages" (YAML + código + tools).
- [ ] 8.2 **Diseño de Arquitectura**:
  - [ ] 8.2.1 Diseñar sistema de contenedores dinámicos para agentes especializados.
  - [ ] 8.2.2 Diseñar sistema de routing basado en selección del usuario (no detección automática).
  - [ ] 8.2.3 Diseñar sistema de gestión de agentes (CRUD, import/export, versionado).

### **9.0 Implementación del Sistema de Agentes Especializados**
- [ ] 9.1 **Infraestructura Base**:
  - [ ] 9.1.1 Crear sistema de contenedores dinámicos para agentes especializados.
  - [ ] 9.1.2 Implementar sistema de discovery y registro de agentes.
  - [ ] 9.1.3 Crear sistema de gestión de configuración YAML para agentes.
- [ ] 9.2 **UI y UX**:
  - [ ] 9.2.1 Modificar UI para mostrar agentes especializados en selector de modelos.
  - [ ] 9.2.2 Crear interfaz de gestión de agentes (agregar, remover, configurar).
  - [ ] 9.2.3 Implementar sistema de import/export de agentes.
- [ ] 9.3 **A2A y Comunicación**:
  - [ ] 9.3.1 Implementar A2A real entre orchestrator y agentes especializados.
  - [ ] 9.3.2 Crear sistema de tools dinámicas para agentes especializados.
  - [ ] 9.3.3 Implementar sistema de capabilities y routing inteligente.

### **10.0 Agentes Especializados de Ejemplo**
- [ ] 10.1 **Agent Data Analyst**:
  - [ ] 10.1.1 Crear contenedor dedicado con tools de análisis de datos.
  - [ ] 10.1.2 Configurar system prompts especializados para análisis estadístico.
  - [ ] 10.1.3 Implementar tools para visualización y reportes.
- [ ] 10.2 **Agent Code Reviewer**:
  - [ ] 10.2.1 Crear contenedor dedicado con tools de análisis de código.
  - [ ] 10.2.2 Configurar system prompts para revisión de código.
  - [ ] 10.2.3 Implementar tools para análisis de seguridad y calidad.

### **11.0 Testing y Validación**
- [ ] 11.1 **Testing del Sistema**:
  - [ ] 11.1.1 Crear tests para sistema de gestión de agentes.
  - [ ] 11.1.2 Validar A2A entre orchestrator y agentes especializados.
  - [ ] 11.1.3 Testear import/export de agentes.
- [ ] 11.2 **Documentación**:
  - [ ] 11.2.1 Documentar proceso de creación de agentes especializados.
  - [ ] 11.2.2 Crear guías para desarrolladores de agentes.
  - [ ] 11.2.3 Documentar API de gestión de agentes.

---

## FASE 1.5: REQUERIMIENTOS DE PRODUCCIÓN

### **12.0 Memoria de Conversación**
- [ ] 12.1 **Configuración de Firestore**:
  - [ ] 12.1.1 Configurar Firestore con PROJECT_PREFIX para multi-tenancy.
  - [ ] 12.1.2 Crear colecciones para memoria de corto, mediano y largo plazo.
  - [ ] 12.1.3 Implementar FirestoreMemory en ADK agents.
- [ ] 12.2 **Memoria de Corto Plazo**:
  - [ ] 12.2.1 Implementar memoria de sesión actual con FirestoreMemory.
  - [ ] 12.2.2 Configurar contexto de conversación en tiempo real.
  - [ ] 12.2.3 Validar persistencia durante la sesión.
- [ ] 12.3 **Memoria de Mediano Plazo**:
  - [ ] 12.3.1 Implementar memoria de conversaciones recientes.
  - [ ] 12.3.2 Configurar límites de retención de conversaciones.
  - [ ] 12.3.3 Implementar búsqueda en historial reciente.
- [ ] 12.4 **Memoria de Largo Plazo**:
  - [ ] 12.4.1 Implementar historial persistente de conversaciones.
  - [ ] 12.4.2 Configurar archivado automático de conversaciones antiguas.
  - [ ] 12.4.3 Implementar recuperación de contexto histórico.

### **13.0 Procesamiento de Archivos**
- [ ] 13.1 **Sistema de Upload**:
  - [ ] 13.1.1 Implementar endpoint de upload en Gateway.
  - [ ] 13.1.2 Configurar validación de tipos de archivo (docs, office, txt, md, imágenes, pdf).
  - [ ] 13.1.3 Implementar límites de tamaño de archivo.
- [ ] 13.2 **Almacenamiento Temporal**:
  - [ ] 13.2.1 Configurar Google Cloud Storage (GCS) para archivos temporales.
  - [ ] 13.2.2 Implementar generación de URLs temporales.
  - [ ] 13.2.3 Configurar limpieza automática de archivos temporales.
- [ ] 13.3 **Procesamiento de Documentos**:
  - [ ] 13.3.1 Integrar Vertex AI para procesamiento de documentos.
  - [ ] 13.3.2 Implementar extracción de texto de PDFs.
  - [ ] 13.3.3 Implementar procesamiento de documentos Office.
- [ ] 13.4 **Procesamiento de Imágenes**:
  - [ ] 13.4.1 Implementar análisis de imágenes adjuntas con Vertex AI.
  - [ ] 13.4.2 Configurar resizing y optimización de imágenes.
  - [ ] 13.4.3 Implementar detección de contenido en imágenes.

### **14.0 Generación de Imágenes**
- [ ] 14.1 **Integración con Vertex AI**:
  - [ ] 14.1.1 Configurar modelo gemini-images para generación.
  - [ ] 14.1.2 Implementar prompts optimizados para generación de imágenes.
  - [ ] 14.1.3 Configurar parámetros de generación (resolución, estilo).
- [ ] 14.2 **Almacenamiento de Imágenes**:
  - [ ] 14.2.1 Configurar GCS para almacenamiento de imágenes generadas.
  - [ ] 14.2.2 Implementar generación de URLs públicas para imágenes.
  - [ ] 14.2.3 Configurar políticas de retención de imágenes.
- [ ] 14.3 **Visualización en UI**:
  - [ ] 14.3.1 Implementar renderizado de imágenes en respuestas de chat.
  - [ ] 14.3.2 Configurar preview de imágenes en la UI.
  - [ ] 14.3.3 Implementar descarga de imágenes generadas.

### **15.0 Testing y Validación de Producción**
- [ ] 15.1 **Testing de Memoria**:
  - [ ] 15.1.1 Validar persistencia de conversaciones entre sesiones.
  - [ ] 15.1.2 Testear memoria de corto, mediano y largo plazo.
  - [ ] 15.1.3 Validar multi-tenancy con diferentes PROJECT_PREFIX.
- [ ] 15.2 **Testing de Archivos**:
  - [ ] 15.2.1 Validar upload de diferentes tipos de archivo.
  - [ ] 15.2.2 Testear procesamiento de documentos complejos.
  - [ ] 15.2.3 Validar análisis de imágenes adjuntas.
- [ ] 15.3 **Testing de Generación de Imágenes**:
  - [ ] 15.3.1 Validar generación de imágenes con diferentes prompts.
  - [ ] 15.3.2 Testear visualización de imágenes en la UI.
  - [ ] 15.3.3 Validar almacenamiento y URLs de imágenes.
- [ ] 15.4 **Testing de Performance**:
  - [ ] 15.4.1 Validar latencia con archivos grandes.
  - [ ] 15.4.2 Testear concurrencia de múltiples usuarios.
  - [ ] 15.4.3 Validar escalabilidad del sistema de memoria.
