"""
Servicio de Memoria Híbrida para CorpChat Gateway.
Combina memoria a corto plazo (Firestore) con memoria a largo plazo (BigQuery).
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import uuid

from google.cloud import firestore
from google.cloud import bigquery
import vertexai
from vertexai.language_models import TextEmbeddingModel

_logger = logging.getLogger(__name__)


class MemoryService:
    """
    Servicio de memoria híbrida que combina:
    - Working Memory (Firestore): Contexto de sesión actual
    - Long-term Memory (BigQuery): Retrieval semántico histórico
    - User Profile (Firestore): Contexto persistente del usuario
    """
    
    def __init__(self, project_id: str):
        """
        Inicializar servicio de memoria.
        
        Args:
            project_id: ID del proyecto GCP
        """
        try:
            self.project_id = project_id
            self.firestore_client = firestore.Client(project=project_id)
            self.bq_client = bigquery.Client(project=project_id)
            
            # Inicializar modelo de embeddings
            location = os.getenv("GOOGLE_CLOUD_LOCATION")
            if not location:
                raise ValueError("GOOGLE_CLOUD_LOCATION environment variable is required")
            vertexai.init(project=project_id, location=location)
            self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            
            # Configuración
            self.collection_prefix = os.getenv("FIRESTORE_COLLECTION_PREFIX", "corpchat")
            
            _logger.info(f"✅ MemoryService inicializado para proyecto {project_id}")
            
        except Exception as e:
            _logger.error(f"❌ Error inicializando MemoryService: {e}", exc_info=True)
            raise
    
    async def get_working_memory(
        self,
        user_id: str,
        session_id: str,
        max_turns: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recupera memoria a corto plazo (últimos N turnos de la sesión actual).
        
        Args:
            user_id: ID del usuario
            session_id: ID de la sesión de chat
            max_turns: Número máximo de turnos a recuperar
        
        Returns:
            Lista de mensajes [{role, content, timestamp}] de turnos recientes
        """
        try:
            _logger.info(f"🧠 Recuperando working memory para usuario {user_id}, sesión {session_id}")
            
            session_ref = self.firestore_client.collection(
                f"{self.collection_prefix}_users/{user_id}/sesiones"
            ).document(session_id)
            
            # Verificar que la sesión existe
            session_doc = session_ref.get()
            if not session_doc.exists:
                _logger.warning(f"⚠️ Sesión {session_id} no encontrada para usuario {user_id}")
                return []
            
            # Recuperar turnos más recientes
            turnos_query = (
                session_ref.collection("turnos")
                .order_by("turn_number", direction=firestore.Query.DESCENDING)
                .limit(max_turns)
            )
            
            turnos = list(turnos_query.stream())
            
            messages = []
            for turno in turnos:
                data = turno.to_dict()
                turn_messages = data.get("messages", [])
                
                # Agregar mensajes del turno
                for msg in turn_messages:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                        "timestamp": msg.get("timestamp", datetime.now().isoformat())
                    })
                
                # Agregar respuesta del asistente
                if "assistant_response" in data:
                    messages.append({
                        "role": "assistant",
                        "content": data["assistant_response"],
                        "timestamp": data.get("timestamp", datetime.now().isoformat())
                    })
            
            # Invertir para orden cronológico
            messages.reverse()
            
            _logger.info(
                f"✅ Working memory recuperada: {len(messages)} mensajes de {len(turnos)} turnos",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "messages_count": len(messages),
                    "labels": {"service": "memory", "team": "corpchat"}
                }
            )
            
            return messages
            
        except Exception as e:
            _logger.error(f"❌ Error recuperando working memory: {e}", exc_info=True)
            return []
    
    async def get_long_term_memory(
        self,
        user_id: str,
        current_query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.7,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Recupera conversaciones pasadas relevantes usando embeddings.
        
        Args:
            user_id: ID del usuario
            current_query: Consulta actual para búsqueda semántica
            max_results: Máximo de conversaciones a recuperar
            similarity_threshold: Umbral de similitud mínima (0.0-1.0)
            days_back: Días hacia atrás para buscar
        
        Returns:
            Lista de contextos relevantes de conversaciones pasadas
        """
        try:
            _logger.info(f"🔍 Búsqueda semántica en long-term memory para: {current_query[:50]}...")
            
            # Generar embedding del query actual
            embeddings = self.embedding_model.get_embeddings([current_query])
            query_embedding = embeddings[0].values
            
            # Búsqueda semántica en BigQuery
            dataset_id = f"{self.project_id}.corpchat"
            table_id = f"{dataset_id}.conversation_memory"
            
            # Verificar que la tabla existe
            try:
                self.bq_client.get_table(table_id)
            except Exception:
                _logger.warning(f"⚠️ Tabla {table_id} no existe, creando...")
                await self._create_conversation_memory_table()
            
            query = f"""
            WITH query_embedding AS (
                SELECT {query_embedding} as embedding
            ),
            similarities AS (
                SELECT
                    user_id,
                    session_id,
                    conversation_text,
                    summary,
                    tags,
                    created_at,
                    turn_count,
                    ML.DISTANCE(embedding, (SELECT embedding FROM query_embedding), 'COSINE') as distance
                FROM `{table_id}`
                WHERE user_id = @user_id
                AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days_back DAY)
                AND embedding IS NOT NULL
            )
            SELECT *
            FROM similarities
            WHERE distance <= @distance_threshold
            ORDER BY distance ASC
            LIMIT @max_results
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                    bigquery.ScalarQueryParameter("distance_threshold", "FLOAT64", 1 - similarity_threshold),
                    bigquery.ScalarQueryParameter("max_results", "INT64", max_results),
                    bigquery.ScalarQueryParameter("days_back", "INT64", days_back)
                ]
            )
            
            query_job = self.bq_client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            contexts = []
            for row in results:
                contexts.append({
                    "text": row.conversation_text,
                    "summary": row.summary,
                    "tags": row.tags or [],
                    "date": row.created_at.isoformat(),
                    "similarity": 1 - row.distance,
                    "session_id": row.session_id,
                    "turn_count": row.turn_count
                })
            
            _logger.info(
                f"✅ Long-term memory: {len(contexts)} contextos relevantes encontrados",
                extra={
                    "user_id": user_id,
                    "query_length": len(current_query),
                    "contexts_found": len(contexts),
                    "similarity_threshold": similarity_threshold,
                    "labels": {"service": "memory", "team": "corpchat"}
                }
            )
            
            return contexts
            
        except Exception as e:
            _logger.error(f"❌ Error en long-term memory: {e}", exc_info=True)
            return []
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Recupera perfil de usuario con contexto persistente.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Perfil del usuario con preferencias y contexto persistente
        """
        try:
            _logger.info(f"👤 Recuperando perfil de usuario: {user_id}")
            
            user_ref = self.firestore_client.collection(f"{self.collection_prefix}_users").document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                # Crear perfil básico si no existe
                profile_data = {
                    "email": user_id,
                    "preferences": {
                        "language": "es",
                        "model_preference": "gemini-fast",
                        "context_window": 10
                    },
                    "context": "",
                    "expertise_areas": [],
                    "recent_projects": [],
                    "total_sessions": 0,
                    "last_activity": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat()
                }
                
                user_ref.set(profile_data)
                _logger.info(f"✅ Perfil de usuario creado para {user_id}")
                
                return profile_data
            
            profile_data = user_doc.to_dict()
            
            _logger.info(f"✅ Perfil de usuario recuperado: {user_id}")
            return profile_data
            
        except Exception as e:
            _logger.error(f"❌ Error recuperando perfil de usuario: {e}", exc_info=True)
            return {
                "email": user_id,
                "preferences": {"language": "es", "model_preference": "gemini-fast"},
                "context": "",
                "expertise_areas": [],
                "recent_projects": []
            }
    
    async def consolidate_session_memory(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Consolida sesión completada en memoria a largo plazo.
        
        Args:
            user_id: ID del usuario
            session_id: ID de la sesión
        
        Returns:
            Resultado de la consolidación
        """
        try:
            _logger.info(f"💾 Consolidando sesión {session_id} para usuario {user_id}")
            
            # Recuperar todos los turnos de la sesión
            session_ref = self.firestore_client.collection(
                f"{self.collection_prefix}_users/{user_id}/sesiones"
            ).document(session_id)
            
            turnos_query = session_ref.collection("turnos").order_by("turn_number")
            turnos = list(turnos_query.stream())
            
            if not turnos:
                _logger.warning(f"⚠️ No hay turnos para consolidar en sesión {session_id}")
                return {"success": False, "reason": "No turnos found"}
            
            # Concatenar conversación completa
            full_conversation = ""
            for turno in turnos:
                data = turno.to_dict()
                
                # Agregar mensajes del turno
                for msg in data.get("messages", []):
                    full_conversation += f"{msg['role']}: {msg['content']}\n"
                
                # Agregar respuesta del asistente
                if "assistant_response" in data:
                    full_conversation += f"assistant: {data['assistant_response']}\n"
                
                full_conversation += "\n"
            
            # Generar embedding de la conversación completa
            embeddings = self.embedding_model.get_embeddings([full_conversation])
            conversation_embedding = embeddings[0].values
            
            # Generar resumen usando Gemini (opcional)
            summary = await self._generate_conversation_summary(full_conversation)
            
            # Extraer tags automáticamente (opcional)
            tags = await self._extract_conversation_tags(full_conversation)
            
            # Almacenar en BigQuery
            dataset_id = f"{self.project_id}.corpchat"
            table_id = f"{dataset_id}.conversation_memory"
            
            row_data = {
                "user_id": user_id,
                "session_id": session_id,
                "conversation_text": full_conversation,
                "embedding": conversation_embedding,
                "summary": summary,
                "tags": tags,
                "created_at": datetime.now().isoformat(),
                "turn_count": len(turnos)
            }
            
            # Insertar en BigQuery
            errors = self.bq_client.insert_rows_json(table_id, [row_data])
            
            if errors:
                _logger.error(f"❌ Error insertando en BigQuery: {errors}")
                return {"success": False, "reason": f"BigQuery error: {errors}"}
            
            # Actualizar perfil de usuario
            user_ref = self.firestore_client.collection(f"{self.collection_prefix}_users").document(user_id)
            user_ref.update({
                "last_session": session_id,
                "total_sessions": firestore.Increment(1),
                "last_activity": datetime.now().isoformat()
            })
            
            # Marcar sesión como consolidada
            session_ref.update({
                "consolidated": True,
                "consolidated_at": datetime.now().isoformat(),
                "summary": summary,
                "tags": tags
            })
            
            _logger.info(
                f"✅ Sesión consolidada exitosamente",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "turn_count": len(turnos),
                    "conversation_length": len(full_conversation),
                    "summary_length": len(summary) if summary else 0,
                    "tags_count": len(tags),
                    "labels": {"service": "memory", "team": "corpchat"}
                }
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "turn_count": len(turnos),
                "conversation_length": len(full_conversation),
                "summary": summary,
                "tags": tags
            }
            
        except Exception as e:
            _logger.error(f"❌ Error consolidando sesión: {e}", exc_info=True)
            return {"success": False, "reason": str(e)}
    
    async def enrich_context(
        self,
        user_id: str,
        session_id: str,
        current_query: str,
        max_working_turns: int = 10,
        max_long_term_results: int = 5
    ) -> str:
        """
        Enriquece contexto con memoria a corto y largo plazo.
        
        Args:
            user_id: ID del usuario
            session_id: ID de la sesión
            current_query: Consulta actual
            max_working_turns: Máximo de turnos de working memory
            max_long_term_results: Máximo de resultados de long-term memory
        
        Returns:
            Contexto enriquecido para el modelo
        """
        try:
            _logger.info(f"🔗 Enriqueciendo contexto para usuario {user_id}")
            
            # 1. Working Memory (corto plazo)
            working_memory = await self.get_working_memory(
                user_id=user_id,
                session_id=session_id,
                max_turns=max_working_turns
            )
            
            # 2. Long-term Memory (largo plazo)
            long_term_context = await self.get_long_term_memory(
                user_id=user_id,
                current_query=current_query,
                max_results=max_long_term_results
            )
            
            # 3. User Profile
            user_profile = await self.get_user_profile(user_id)
            
            # 4. Construir contexto enriquecido
            enhanced_context = self._build_enhanced_context(
                working_memory=working_memory,
                long_term_context=long_term_context,
                user_profile=user_profile,
                current_query=current_query
            )
            
            _logger.info(
                f"✅ Contexto enriquecido construido",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "working_messages": len(working_memory),
                    "long_term_contexts": len(long_term_context),
                    "context_length": len(enhanced_context),
                    "labels": {"service": "memory", "team": "corpchat"}
                }
            )
            
            return enhanced_context
            
        except Exception as e:
            _logger.error(f"❌ Error enriqueciendo contexto: {e}", exc_info=True)
            return current_query  # Fallback a query original
    
    def _build_enhanced_context(
        self,
        working_memory: List[Dict[str, Any]],
        long_term_context: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        current_query: str
    ) -> str:
        """
        Construye contexto enriquecido combinando todas las fuentes.
        
        Args:
            working_memory: Memoria a corto plazo
            long_term_context: Contexto histórico relevante
            user_profile: Perfil del usuario
            current_query: Consulta actual
        
        Returns:
            Contexto enriquecido formateado
        """
        context_parts = []
        
        # 1. Información del usuario
        if user_profile.get("expertise_areas"):
            context_parts.append(f"Áreas de expertise del usuario: {', '.join(user_profile['expertise_areas'])}")
        
        if user_profile.get("context"):
            context_parts.append(f"Contexto persistente: {user_profile['context']}")
        
        # 2. Contexto histórico relevante
        if long_term_context:
            context_parts.append("Contexto de conversaciones anteriores relevantes:")
            for ctx in long_term_context[:3]:  # Máximo 3 contextos históricos
                summary = ctx.get("summary", ctx["text"][:200] + "...")
                date = ctx["date"][:10]  # Solo fecha
                similarity = ctx["similarity"]
                context_parts.append(f"- {date} (relevancia: {similarity:.2f}): {summary}")
        
        # 3. Conversación actual
        if working_memory:
            context_parts.append("Conversación actual:")
            for msg in working_memory[-6:]:  # Últimos 6 mensajes
                role = "Usuario" if msg["role"] == "user" else "Asistente"
                content = msg["content"][:300] + "..." if len(msg["content"]) > 300 else msg["content"]
                context_parts.append(f"{role}: {content}")
        
        # 4. Consulta actual
        context_parts.append(f"Consulta actual: {current_query}")
        
        return "\n\n".join(context_parts)
    
    async def _create_conversation_memory_table(self):
        """Crea la tabla de memoria a largo plazo en BigQuery."""
        try:
            dataset_id = f"{self.project_id}.corpchat"
            table_id = f"{dataset_id}.conversation_memory"
            
            schema = [
                bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("conversation_text", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
                bigquery.SchemaField("summary", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("turn_count", "INT64", mode="REQUIRED")
            ]
            
            table = bigquery.Table(table_id, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="created_at"
            )
            table.clustering_fields = ["user_id", "session_id"]
            
            table = self.bq_client.create_table(table)
            _logger.info(f"✅ Tabla {table_id} creada exitosamente")
            
        except Exception as e:
            _logger.error(f"❌ Error creando tabla de memoria: {e}", exc_info=True)
            raise
    
    async def _generate_conversation_summary(self, conversation: str) -> str:
        """
        Genera resumen de la conversación usando Gemini.
        
        Args:
            conversation: Texto completo de la conversación
        
        Returns:
            Resumen de la conversación
        """
        try:
            if len(conversation) < 100:  # Conversaciones muy cortas no necesitan resumen
                return ""
            
            # Usar Gemini para generar resumen
            model = GenerativeModel("gemini-1.5-flash-001")
            
            prompt = f"""
            Resume la siguiente conversación en máximo 2 oraciones, enfocándote en los temas principales discutidos:
            
            {conversation}
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            _logger.warning(f"⚠️ Error generando resumen: {e}")
            return ""
    
    async def _extract_conversation_tags(self, conversation: str) -> List[str]:
        """
        Extrae tags automáticamente de la conversación.
        
        Args:
            conversation: Texto completo de la conversación
        
        Returns:
            Lista de tags relevantes
        """
        try:
            # Tags por defecto basados en palabras clave
            default_tags = []
            
            # Detectar temas técnicos
            tech_keywords = {
                "ia": ["inteligencia artificial", "ia", "ai", "gemini", "modelo"],
                "desarrollo": ["código", "programar", "desarrollo", "api", "software"],
                "documentos": ["archivo", "documento", "pdf", "excel", "word"],
                "datos": ["datos", "base de datos", "bigquery", "firestore"],
                "negocio": ["empresa", "proyecto", "cliente", "negocio"]
            }
            
            conversation_lower = conversation.lower()
            for tag, keywords in tech_keywords.items():
                if any(keyword in conversation_lower for keyword in keywords):
                    default_tags.append(tag)
            
            return default_tags[:5]  # Máximo 5 tags
            
        except Exception as e:
            _logger.warning(f"⚠️ Error extrayendo tags: {e}")
            return []
