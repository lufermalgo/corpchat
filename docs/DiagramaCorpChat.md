┌─────────────────────────────────────────────────────────────────────────────┐
│                        CORPCHAT DOCUMENT PIPELINE                           │
│                            (Open WebUI + Backend)                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐
│   USUARIO       │    │   OPEN WEBUI     │    │     CORPCHAT GATEWAY        │
│                 │    │  (Cloud Run)     │    │     (Cloud Run)             │
│ • Sube PDF      │───▶│                  │───▶│                             │
│ • Hace pregunta │    │ • Auth Google    │    │ • Model Selector            │
│                 │    │ • UI Chat        │    │ • RAG Search                │
│                 │    │ • Document UI    │    │ • LLM Processing            │
└─────────────────┘    └──────────────────┘    └─────────────────────────────┘
                                │                           │
                                ▼                           ▼
                    ┌──────────────────┐    ┌─────────────────────────────┐
                    │ CORPCHAT INGESTOR│    │     VERTEX AI GEMINI        │
                    │   (Cloud Run)    │    │                             │
                    │                  │    │ • gemini-2.5-flash          │
                    │ • PDF Extractor  │    │ • gemini-2.5-pro            │
                    │ • DOCX Extractor │    │ • gemini-2.5-flash-image    │
                    │ • XLSX Extractor │    │ • text-embedding-004        │
                    │ • Image OCR      │    │                             │
                    │ • Chunking       │    │                             │
                    └──────────────────┘    └─────────────────────────────┘
                                │                           ▲
                                ▼                           │
                    ┌──────────────────┐                    │
                    │  CLOUD STORAGE   │                    │
                    │                  │                    │
                    │ • PDFs por user  │                    │
                    │ • Metadatos      │                    │
                    │ • Conversaciones │                    │
                    └──────────────────┘                    │
                                │                           │
                                ▼                           │
                    ┌──────────────────┐                    │
                    │    BIGQUERY      │                    │
                    │                  │                    │
                    │ • embeddings     │                    │
                    │ • metadata       │                    │
                    │ • vector search  │                    │
                    └──────────────────┘                    │
                                │                           │
                                └───────────────────────────┘
                                           │
                                           ▼
                                ┌──────────────────┐
                                │   FIRESTORE      │
                                │                  │
                                │ • User sessions  │
                                │ • Chat history   │
                                │ • Metadata       │
                                └──────────────────┘

FLUJO DE DOCUMENTOS:
1. Usuario sube PDF → Open WebUI
2. Open WebUI → CorpChat Ingestor (/extract/process)
3. Ingestor extrae texto → Chunking → Embeddings
4. Embeddings → BigQuery Vector Store
5. Documento original → Cloud Storage

FLUJO DE CONSULTAS:
1. Usuario pregunta → Open WebUI
2. Open WebUI → CorpChat Gateway (/chat/completions)
3. Gateway busca en BigQuery → RAG Context
4. Gateway + RAG → Vertex AI Gemini
5. Respuesta → Open WebUI → Usuario