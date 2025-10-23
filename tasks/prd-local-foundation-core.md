# PRD: Fase 1 - Fundación Arquitectónica del Core (Modelo Canónico 2.0)

- **Feature Name**: Core Architectural Foundation (Canonical Model 2.0)
- **Date**: 2025-10-22

## 1. Introduction/Overview

Este documento describe los requisitos para la **Fase 1: Fundación Arquitectónica de la Plataforma**. El objetivo es construir el esqueleto funcional completo del sistema, siguiendo estrictamente el **Modelo Canónico 2.0** definido en el documento de arquitectura. El entregable será un entorno Docker local completamente funcional que implementa el flujo `UI -> Gateway -> Orquestador -> Agente`, sentando una base de código limpia, escalable y mantenible para todas las fases futuras.

## 2. Goals

-   **G1**: Implementar la estructura de directorios canónica, separando `config` y `services`.
-   **G2**: Construir y configurar los **4 servicios Docker**: `gateway`, `ui`, `orchestrator`, y `agent-generalist`.
-   **G3**: Establecer el flujo de comunicación correcto: La `ui` debe hablar **exclusivamente** con el `gateway`.
-   **G4**: Implementar el patrón de código de backend compartido, con una imagen Docker única para los servicios ADK.
-   **G5**: Habilitar el nombrado dinámico de todos los recursos a través de la variable `PROJECT_PREFIX`.
-   **G6**: Integrar la autenticación con Google OAuth y el branding corporativo básico.

## 3. Functional Requirements

### 3.1. Estructura y Configuración del Entorno
-   **FR1.1**: Se debe crear la estructura de directorios `/config/{orchestrator,agent-generalist}` y `/services/{gateway,ui,backend}`.
-   **FR1.2**: El fichero `.env` debe definir la variable `PROJECT_PREFIX`.
-   **FR1.3**: El `docker-compose.yml` debe definir los 4 servicios (`gateway`, `ui`, `orchestrator`, `agent-generalist`).
-   **FR1.4**: Todos los nombres de contenedores, redes y otros recursos deben usar `PROJECT_PREFIX`.

### 3.2. Servicio: Gateway (`${PROJECT_PREFIX}-gateway`)
-   **FR2.1**: Debe ser un servicio Nginx.
-   **FR2.2**: Debe escuchar en un puerto público (ej. `8080`) y reenviar las peticiones de `/v1/chat/completions` al servicio `orchestrator`.

### 3.3. Servicio: UI (`${PROJECT_PREFIX}-ui`)
-   **FR3.1**: Debe ser una imagen derivada de Open WebUI con branding personalizado.
-   **FR3.2**: Debe configurarse para apuntar **únicamente** al servicio `gateway` (`OPENAI_API_BASE_URL="http://gateway"`).
-   **FR3.3**: Debe tener la autenticación OIDC de Google configurada.

### 3.4. Servicios de Backend (`orchestrator` y `agent-generalist`)
-   **FR4.1**: Ambos servicios deben construirse a partir del `Dockerfile` único en `services/backend`.
-   **FR4.2**: El `docker-compose.yml` debe montar la configuración específica de cada servicio desde `/config/{service_name}`.
-   **FR4.3**: El `orchestrator` debe exponer un puerto interno para el `gateway` y gestionar la memoria con `FirestoreMemory` (usando `PROJECT_PREFIX` para el nombre de la colección).
-   **FR4.4**: El `agent-generalist` debe exponer un puerto interno para A2A y contener la lógica para llamar a las APIs de Vertex AI.
-   **FR4.5**: La comunicación entre `orchestrator` y `agent-generalist` debe ser vía A2A.

## 4. Requerimientos de Producción (Fase 1.5)

### 4.1. Memoria de Conversación
- **FR5.1**: Implementar memoria de corto plazo (sesión actual) con FirestoreMemory
- **FR5.2**: Implementar memoria de mediano plazo (conversaciones recientes) con Firestore
- **FR5.3**: Implementar memoria de largo plazo (historial persistente) con Firestore
- **FR5.4**: Configurar colecciones Firestore con `PROJECT_PREFIX` para multi-tenancy

### 4.2. Procesamiento de Archivos
- **FR6.1**: Implementar upload de archivos (docs, office, txt, md, imágenes, pdf)
- **FR6.2**: Implementar procesamiento de documentos con Vertex AI
- **FR6.3**: Implementar procesamiento de imágenes adjuntas en conversaciones
- **FR6.4**: Implementar almacenamiento temporal de archivos en GCS
- **FR6.5**: Implementar limpieza automática de archivos temporales

### 4.3. Generación de Imágenes
- **FR7.1**: Implementar generación de imágenes con modelo gemini-images
- **FR7.2**: Implementar visualización de imágenes generadas en la UI
- **FR7.3**: Implementar almacenamiento de imágenes generadas en GCS
- **FR7.4**: Implementar gestión de URLs de imágenes en respuestas

## 5. Non-Goals (Out of Scope)

-   Agentes especializados más allá del `agent-generalist` (esto se abordará en una fase posterior).
-   Sistema de gestión dinámica de agentes especializados (esto se abordará en una fase posterior).

## 4.1. Consideraciones Futuras para Agentes Especializados

**Problema Identificado**: La arquitectura actual no es escalable para agentes especializados reales. El enfoque actual de "detección dinámica" no es apropiado para agentes especializados que requieren:

- **Selección explícita del usuario**: Los agentes especializados deben ser seleccionables desde la UI (ej: `agent-data-analyst`, `agent-code-reviewer`).
- **Contenedores dedicados**: Cada agente especializado debe tener su propio contenedor con sus herramientas específicas.
- **Configuración completa**: Cada agente debe tener su configuración completa (tools, system prompts, capabilities) en archivos YAML.
- **A2A real**: Comunicación real entre agentes usando el protocolo A2A de ADK.
- **Gestión dinámica**: Sistema para agregar/remover agentes sin modificar código.

**Solución Propuesta para Fase Futura**:
- Modelos en UI: `gemini-fast`, `gemini-thinking`, `gemini-images` + `agent-data-analyst`, `agent-code-reviewer`, etc.
- Cada agente especializado: contenedor dedicado + configuración YAML completa + tools específicas.
- Orchestrator: routing basado en selección del usuario, no en detección automática.
- Sistema de gestión: similar a Open WebUI para importar/exportar agentes.

## 6. Success Metrics

### 6.1. Métricas Base (Fase 1)
-   El entorno se levanta con un solo comando (`docker-compose up`).
-   Una petición de chat desde la UI traza correctamente el flujo `UI -> Gateway -> Orchestrator -> Agent -> Vertex AI` y viceversa, lo cual es verificable en los logs.
-   Cambiar el `PROJECT_PREFIX` en el `.env` y reiniciar los contenedores resulta en un sistema funcional con todos los recursos renombrados.

### 6.2. Métricas de Producción (Fase 1.5)
-   Las conversaciones persisten entre sesiones (memoria de largo plazo).
-   Los archivos adjuntos se procesan correctamente y se muestran en la UI.
-   Las imágenes generadas se visualizan correctamente en la UI.
-   El sistema maneja múltiples tipos de archivos sin errores.
-   La memoria de conversación funciona correctamente con múltiples usuarios.
