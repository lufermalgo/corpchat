# Arquitectura de la Plataforma de IA Conversacional "CorpChat"

**Versión:** 2.0 (Modelo Canónico)
**Fecha:** 2025-10-22

---

## 1. Visión y Experiencia del Producto

### 1.1. ¿Qué Estamos Construyendo y por Qué?

Estamos construyendo una plataforma de IA conversacional de nivel enterprise. El **problema** que resuelve es la fragmentación del conocimiento y la necesidad de herramientas de IA seguras y contextualizadas dentro de la organización. Los empleados recurren a herramientas públicas (ChatGPT, Gemini) con datos potencialmente sensibles y sin acceso al conocimiento interno.

La plataforma soluciona esto proporcionando un asistente de IA centralizado, seguro y multi-modal, que actúa como un "sistema operativo" para la inteligencia corporativa. El objetivo es que se convierta en la herramienta principal para la consulta de información, la generación de contenido y la automatización de tareas, aumentando la productividad y protegiendo la propiedad intelectual.

### 1.2. Perfil del Usuario y sus Necesidades

La plataforma está diseñado para **todos los empleados de la organización**, desde roles directivos hasta operativos. Esto incluye perfiles diversos:

*   **Analistas**: Necesitan respuestas rápidas basadas en datos de negocio.
*   **Desarrolladores**: Requieren generación y depuración de código.
*   **Equipos de Ventas y Marketing**: Necesitan crear borradores de correos, propuestas y analizar documentos.
*   **Dirección**: Busca resúmenes ejecutivos y análisis de tendencias.

Todos comparten una necesidad común: **una herramienta potente, intuitiva y fiable que entienda el contexto de su trabajo.**

### 1.3. La Experiencia del Usuario (UX)

La interacción con la plataforma debe ser fluida, intuitiva y comparable a las mejores plataformas del mercado.

1.  **Login Unificado**: El usuario accede a través de su cuenta de Google corporativa, sin necesidad de nuevas credenciales.
2.  **Interfaz Clara y Personalizable**: La UI, basada en Open WebUI, presenta un diseño limpio. El usuario ve el branding de la compañía ("CorpChat") y tiene la opción de seleccionar su modo de trabajo a través de una lista de "Modelos".
3.  **Selección de "Modelo"**: El usuario puede elegir entre diferentes motores de IA, cada uno optimizado para una tarea:
    *   `Gemini-Fast`: Para respuestas rápidas.
    *   `Gemini-Thinking`: Para razonamiento complejo.
    *   `Gemini-Images`: Para la generación de imágenes.
    *(Esta lista es dinámica y se gestiona centralizadamente)*.
4.  **Conversación Multi-Modal**: El usuario puede escribir, **dictar por voz** y **adjuntar ficheros** (PDF, DOCX, imágenes) directamente en el chat.
5.  **Interacción Contextual**: La plataforma mantiene la memoria de la conversación, permitiendo diálogos largos y coherentes. Cuando se adjunta un documento, el usuario puede "hablar" con él, haciendo preguntas y pidiendo resúmenes.
6.  **Feedback Continuo**: Para tareas largas (como procesar un documento), la UI muestra el estado en tiempo real ("Procesando...", "Generando embeddings...") gracias a los callbacks del backend.

### 1.4. Criterios de Éxito del Producto

El éxito de la plataforma se medirá por:

*   **Adopción**: Porcentaje de empleados que utilizan la plataforma semanalmente (WAU).
*   **Engagement**: Profundidad de uso, medido por el número de conversaciones por sesión y el porcentaje de interacciones multi-modales (adjuntos, dictado por voz).
*   **Calidad Percibida**: Puntuaciones de satisfacción del usuario (NPS interno) y tasa de respuestas calificadas como "útiles".
*   **Rendimiento**: La latencia P95 para una respuesta de texto debe ser inferior a 3 segundos.
*   **Fiabilidad**: Tasa de éxito de las interacciones superior al 99.5%.

---

## 2. Arquitectura Técnica (Modelo Canónico 2.0)

La arquitectura está diseñada para cumplir con los principios de modularidad, escalabilidad y replicabilidad.

### 2.1. Estructura de Directorios y Servicios

Se define un modelo con **código de backend centralizado** y **configuración por servicio**, orquestado por Docker Compose.

*   **Estructura de Ficheros**:
    ```
    /
    ├── config/
    │   ├── orchestrator/
    │   └── agent-generalist/
    ├── services/
    │   ├── gateway/
    │   ├── ui/
    │   └── backend/
    └── docker-compose.yml
    ```
*   **Servicios en Ejecución (4)**:
    1.  `gateway`: Proxy Nginx. **Punto de entrada único para la UI**.
    2.  `ui`: Open WebUI con branding.
    3.  `orchestrator`: Agente ADK que gestiona la lógica de negocio.
    4.  `agent-generalist`: Agente ADK que ejecuta las tareas de IA.

### 2.2. Diagrama de Flujo y Componentes

```mermaid
graph TD
    subgraph "Capa de Cliente & Red"
        U[Usuario] --> UI[Open WebUI]
        UI -- "1. Petición a api.corpchat.com" --> GW[API Gateway (Nginx)]
    end

    subgraph "Capa de Lógica de Negocio (ADK)"
        GW -- "2. Reenvía a Orquestador" --> ORCH[Orquestador Principal]
        ORCH -- "3. Lee Configuración" --> CONF[Config Dinámica (Firestore)]
        ORCH -- "4. Delega Tarea (A2A)" --> AGENT_GEN[Agente Generalista]
    end
    
    subgraph "Capa de Ejecución y Datos"
        AGENT_GEN -- "5. Selecciona y usa Tool" --> VAI[Vertex AI APIs]
        ORCH -- "Gestiona Memoria" --> MEM[Memoria de Chat (Firestore)]
    end

    VAI -- "6. Respuesta del Modelo" --> AGENT_GEN
    AGENT_GEN -- "7. Devuelve resultado" --> ORCH
    ORCH -- "8. Devuelve a Gateway" --> GW
    GW -- "9. Devuelve a UI" --> UI
    UI -- "10. Muestra a Usuario" --> U
```

### 2.3. Principios de Diseño Técnico

*   **Punto de Entrada Único**: La UI **siempre** se comunica con el `gateway`, que actúa como proxy inverso. Esto desacopla la UI de la ubicación de los servicios de backend.
*   **Configuración Dinámica de Modelos**: El `orchestrator` lee una configuración en Firestore para saber qué "modelos" están disponibles y a qué agente debe enrutar cada uno. Esto permite añadir o modificar modelos sin redesplegar código.
*   **Separación de Responsabilidades**:
    *   `gateway`: Gestiona el tráfico de red.
    *   `orchestrator`: Gestiona la sesión, la memoria y la lógica de negocio (qué agente usar).
    *   `agent-generalist`: Ejecuta la interacción técnica con las APIs de IA.
*   **Código Backend Reutilizable**: Todos los servicios ADK se construyen desde una imagen Docker común (`services/backend`) para evitar la duplicación de código. La configuración específica de cada servicio se monta desde el directorio `/config`.
*   **Nombrado Dinámico (`PROJECT_PREFIX`)**: Todos los recursos (contenedores, redes, estructura de directorios el proyecto, colecciones de BBDD) se nombran con un prefijo definido en el `.env`, garantizando la replicabilidad del proyecto.

---
*(Otras secciones como el Catálogo de Agentes, Estrategia de Terminación, etc., se mantienen como se definieron anteriormente)*
