"""
Servicio de Speech-to-Text (STT) para CorpChat Gateway.
Utiliza Google Cloud Speech-to-Text API para transcripción de alta calidad.
"""

import os
import logging
import asyncio
import math
from typing import Dict, Optional, List
from google.cloud import speech
import vertexai
from vertexai.language_models import TextEmbeddingModel

_logger = logging.getLogger(__name__)


class STTService:
    """
    Servicio de transcripción de audio usando Google Cloud Speech-to-Text.
    """
    
    def __init__(self):
        """Inicializar cliente de Speech-to-Text."""
        try:
            self.client = speech.SpeechClient()
            
            # Labels para billing tracking de CorpChat
            self.billing_labels = {
                "project": "corpchat",
                "service": "stt", 
                "team": "corpchat-dev"
            }
            
            _logger.info("✅ Cliente Speech-to-Text inicializado correctamente")
        except Exception as e:
            _logger.error(f"❌ Error inicializando Speech-to-Text: {e}", exc_info=True)
            raise
    
    async def transcribe_audio(
        self,
        audio_content: bytes,
        language_code: str = "es-ES",
        enable_automatic_punctuation: bool = True,
        model: str = "latest_long",
        enable_word_time_offsets: bool = False,
        enable_word_confidence: bool = True
    ) -> Dict[str, any]:
        """
        Transcribe audio usando Google Cloud Speech-to-Text.
        
        Args:
            audio_content: Audio en bytes (WAV, FLAC, MP3, etc.)
            language_code: Código de idioma (es-ES, en-US, pt-BR)
            enable_automatic_punctuation: Puntuación automática
            model: Modelo de STT (latest_long para mejor calidad con gramática)
            enable_word_time_offsets: Incluir timestamps por palabra
            enable_word_confidence: Incluir confianza por palabra
        
        Returns:
            {
                "transcript": "texto transcrito",
                "confidence": 0.95,
                "language": "es-ES",
                "words": [{"word": "hola", "confidence": 0.98, "start_time": 1.0}],
                "model_used": "latest_long"
            }
        """
        try:
            # Configurar audio
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Detectar formato de audio y configurar encoding apropiado
            audio_info = self.detect_audio_format(audio_content)
            encoding = self._get_audio_encoding(audio_info["format"])
            
            # Configurar reconocimiento optimizado para alta calidad
            config = speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,  # Forzar puntuación automática
                model=model,  # Se actualizará dinámicamente según duración
                use_enhanced=True,  # Usar modelo mejorado
                enable_word_time_offsets=enable_word_time_offsets,
                enable_word_confidence=enable_word_confidence,
                # Configuración de contexto para mejor precisión
                speech_contexts=[
                    speech.SpeechContext(
                        phrases=[
                            # Términos técnicos de CorpChat
                            "CorpChat", "Gemini", "inteligencia artificial", "IA",
                            "Google Cloud", "BigQuery", "Firestore", "Cloud Storage",
                            "Vertex AI", "ADK", "multi-agente", "RAG",
                            "embeddings", "vector search", "chunking", "pipeline",
                            "streaming", "API", "endpoint", "microservicio",
                            "FinOps", "serverless", "Cloud Run", "Terraform",
                            "autenticación", "autorización", "JWT", "OAuth",
                            # Términos comunes en español
                            "español", "inglés", "portugués", "transcripción",
                            "documento", "archivo", "proyecto", "empresa",
                            "reunión", "presentación", "análisis", "reporte",
                            "cliente", "usuario", "sistema", "plataforma",
                            "desarrollo", "implementación", "configuración", "deployment"
                        ],
                        boost=15.0  # Boost alto para mejor reconocimiento
                    )
                ],
                # Configuraciones adicionales para mejor calidad
                alternative_language_codes=["en-US", "pt-BR"],
                max_alternatives=1,
                profanity_filter=False  # Deshabilitar para no perder palabras técnicas
            )
            
            # Determinar modelo y método basado en duración estimada más precisa
            # Para MP3: ~128kbps = ~16KB/s, para WAV: 16kHz * 16bit * 1 canal = 32KB/s
            if audio_info["format"] == "MP3":
                estimated_duration = len(audio_content) / (128 * 1024 / 8)  # 128kbps en bytes/segundo
            else:
                estimated_duration = len(audio_content) / (16000 * 2)  # 16kHz, 16-bit, mono
            
            _logger.info(f"📊 Audio: {audio_info['format']}, {audio_info['size_mb']:.2f}MB, duración estimada: {estimated_duration:.1f}s")
            
            # Configurar modelo apropiado según duración (según documentación Google)
            if estimated_duration <= 30:  # Audio corto (según documentación latest_short < 30s)
                model_name = "latest_short"  # Optimizado para audios cortos
                use_long_running = False
                _logger.info(f"🔄 Audio corto detectado ({estimated_duration:.1f}s), usando latest_short...")
            elif estimated_duration <= 600:  # Audio largo (hasta 10 minutos)
                model_name = "latest_long"  # Optimizado para audios largos
                use_long_running = True
                _logger.info(f"🔄 Audio largo detectado ({estimated_duration:.1f}s), usando latest_long...")
            else:  # Audio demasiado largo
                _logger.warning(f"⚠️ Audio demasiado largo ({estimated_duration:.1f}s), máximo permitido: 600s")
                transcription_result = {
                    "transcript": "",
                    "confidence": 0.0,
                    "language": language_code,
                    "words": [],
                    "model_used": "none",
                    "error": "Audio demasiado largo",
                    "message": "El dictado no puede exceder 10 minutos. Por favor, divide tu mensaje en partes más cortas.",
                    "max_duration": 600,
                    "method": "rejected"
                }
                return transcription_result
            
            # Actualizar configuración con modelo apropiado
            config.model = model_name
            
            # Logging con modelo correcto
            _logger.info(f"🎤 Iniciando transcripción con modelo {model_name} para idioma {language_code}")
            
            if use_long_running:
                # Usar long_running_recognize para archivos largos
                operation = self.client.long_running_recognize(config=config, audio=audio)
                _logger.info("⏳ Esperando transcripción asíncrona...")
                
                # Esperar hasta 300 segundos (5 minutos) para la transcripción
                response = operation.result(timeout=300)
                
                if not response.results:
                    _logger.warning("⚠️ No se obtuvieron resultados de transcripción (long_running)")
                    return {
                        "transcript": "",
                        "confidence": 0.0,
                        "language": language_code,
                        "words": [],
                        "model_used": model_name,
                        "error": "No se detectó habla en el audio (long_running)",
                        "method": "long_running_recognize"
                    }
                
                # Para long_running, concatenar todos los resultados
                full_transcript = ""
                total_confidence = 0.0
                word_count = 0
                
                for result in response.results:
                    if result.alternatives:
                        alternative = result.alternatives[0]
                        full_transcript += alternative.transcript + " "
                        total_confidence += alternative.confidence
                        word_count += 1
                        
                        # Agregar palabras si están disponibles
                        if hasattr(alternative, 'words') and alternative.words:
                            for word_info in alternative.words:
                                word_data = {
                                    "word": word_info.word,
                                    "confidence": getattr(word_info, 'confidence', 0.0),
                                    "start_time": word_info.start_time.total_seconds() if hasattr(word_info, 'start_time') else None,
                                    "end_time": word_info.end_time.total_seconds() if hasattr(word_info, 'end_time') else None
                                }
                                words.append(word_data)
                
                # Calcular confianza promedio
                avg_confidence = total_confidence / word_count if word_count > 0 else 0.0
                
                transcription_result = {
                    "transcript": full_transcript.strip(),
                    "confidence": avg_confidence,
                    "language": language_code,
                    "words": words,
                    "model_used": model_name,
                    "is_final": True,
                    "method": "long_running_recognize",
                    "duration_seconds": estimated_duration
                }
                
            else:
                # Usar recognize() para archivos cortos con latest_short
                _logger.info("🔄 Enviando audio corto a Speech-to-Text API...")
                response = self.client.recognize(config=config, audio=audio)
                
                if not response.results:
                    _logger.warning("⚠️ No se obtuvieron resultados de transcripción")
                    return {
                        "transcript": "",
                        "confidence": 0.0,
                        "language": language_code,
                        "words": [],
                        "model_used": model_name,
                        "error": "No se detectó habla en el audio",
                        "method": "recognize"
                    }
                
                # Procesar resultados
                result = response.results[0]
                alternative = result.alternatives[0]
                
                # Extraer palabras con timestamps si están disponibles
                words = []
                if hasattr(alternative, 'words') and alternative.words:
                    for word_info in alternative.words:
                        word_data = {
                            "word": word_info.word,
                            "confidence": getattr(word_info, 'confidence', 0.0),
                            "start_time": word_info.start_time.total_seconds() if hasattr(word_info, 'start_time') else None,
                            "end_time": word_info.end_time.total_seconds() if hasattr(word_info, 'end_time') else None
                        }
                        words.append(word_data)
                
                transcription_result = {
                    "transcript": alternative.transcript,
                    "confidence": alternative.confidence,
                    "language": language_code,
                    "words": words,
                    "model_used": model_name,
                    "is_final": True,
                    "method": "recognize"
                }
            
            # Logging de calidad de transcripción
            _logger.info(
                f"✅ Transcripción completada - Calidad: {transcription_result['confidence']:.2f}",
                extra={
                    "transcript_length": len(transcription_result["transcript"]),
                    "confidence": transcription_result["confidence"],
                    "language": language_code,
                    "model": model_name,
                    "method": transcription_result.get("method", "unknown"),
                    "words_count": len(transcription_result["words"]),
                    "duration_seconds": estimated_duration,
                    "transcript_preview": transcription_result["transcript"][:100] + "..." if len(transcription_result["transcript"]) > 100 else transcription_result["transcript"],
                    "quality_assessment": "Excelente" if transcription_result["confidence"] > 0.9 else "Buena" if transcription_result["confidence"] > 0.7 else "Regular" if transcription_result["confidence"] > 0.5 else "Mala",
                    "labels": {
                        "service": "stt", 
                        "team": "corpchat",
                        "project": "corpchat",
                        "billing_project": "corpchat",
                        "billing_service": "speech_to_text",
                        "billing_team": "corpchat-dev"
                    }
                }
            )
            
            return transcription_result
            
    except Exception as e:
        _logger.error(f"❌ Error en transcripción: {e}", exc_info=True)
        return {
            "transcript": "",
            "confidence": 0.0,
            "language": language_code,
            "words": [],
            "model_used": model,
            "error": str(e)
        }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Obtiene lista de idiomas soportados.
        
        Returns:
            Diccionario con códigos de idioma y nombres
        """
        return {
            "es-ES": "Español (España)",
            "es-MX": "Español (México)",
            "es-AR": "Español (Argentina)",
            "es-CO": "Español (Colombia)",
            "en-US": "English (United States)",
            "en-GB": "English (United Kingdom)",
            "pt-BR": "Português (Brasil)",
            "pt-PT": "Português (Portugal)",
            "fr-FR": "Français (France)",
            "de-DE": "Deutsch (Deutschland)",
            "it-IT": "Italiano (Italia)",
            "ja-JP": "日本語 (日本)",
            "ko-KR": "한국어 (대한민국)",
            "zh-CN": "中文 (中国)",
            "zh-TW": "中文 (台灣)"
        }
    
    def get_available_models(self) -> Dict[str, str]:
        """
        Obtiene modelos disponibles de Speech-to-Text.
        
        Returns:
            Diccionario con modelos y descripciones
        """
        return {
            "latest_long": "Mejor modelo para audio largo con gramática avanzada",
            "latest_short": "Optimizado para audio corto",
            "phone_call": "Optimizado para llamadas telefónicas",
            "video": "Optimizado para video",
            "command_and_search": "Optimizado para comandos y búsquedas",
            "default": "Modelo por defecto"
        }
    
    def _get_audio_encoding(self, format_type: str) -> speech.RecognitionConfig.AudioEncoding:
        """
        Mapea formato de audio detectado a encoding de Google Cloud Speech-to-Text.
        
        Args:
            format_type: Tipo de formato detectado (WAV, MP3, FLAC, OGG)
        
        Returns:
            AudioEncoding apropiado para Google Cloud Speech-to-Text
        """
        encoding_map = {
            "WAV": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "MP3": speech.RecognitionConfig.AudioEncoding.MP3,
            "FLAC": speech.RecognitionConfig.AudioEncoding.FLAC,
            "OGG": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            "UNKNOWN": speech.RecognitionConfig.AudioEncoding.LINEAR16  # Fallback
        }
        
        return encoding_map.get(format_type.upper(), speech.RecognitionConfig.AudioEncoding.LINEAR16)
    
    def detect_audio_format(self, audio_content: bytes) -> Dict[str, any]:
        """
        Detecta formato y características del audio.
        
        Args:
            audio_content: Contenido de audio en bytes
        
        Returns:
            Información sobre el formato de audio
        """
        try:
            # Detectar formato por magic bytes
            if audio_content.startswith(b'RIFF'):
                format_type = "WAV"
            elif audio_content.startswith(b'ID3') or audio_content.startswith(b'\xff\xfb'):
                format_type = "MP3"
            elif audio_content.startswith(b'fLaC'):
                format_type = "FLAC"
            elif audio_content.startswith(b'OggS'):
                format_type = "OGG"
            else:
                format_type = "UNKNOWN"
            
            return {
                "format": format_type,
                "size_bytes": len(audio_content),
                "size_mb": round(len(audio_content) / (1024 * 1024), 2),
                "is_supported": format_type in ["WAV", "MP3", "FLAC", "OGG"]
            }
            
        except Exception as e:
            _logger.error(f"❌ Error detectando formato de audio: {e}")
            return {
                "format": "UNKNOWN",
                "size_bytes": len(audio_content),
                "size_mb": round(len(audio_content) / (1024 * 1024), 2),
                "is_supported": False,
                "error": str(e)
            }
    
    async def transcribe_with_enhanced_context(
        self,
        audio_content: bytes,
        context_phrases: list = None,
        user_id: str = None,
        language_code: str = "es-ES"
    ) -> Dict[str, any]:
        """
        Transcripción con contexto mejorado basado en el usuario.
        
        Args:
            audio_content: Audio en bytes
            context_phrases: Frases específicas del contexto del usuario
            user_id: ID del usuario para contexto personalizado
            language_code: Código de idioma
        
        Returns:
            Resultado de transcripción con contexto mejorado
        """
        try:
            _logger.info(f"🎤 Transcripción con contexto mejorado para usuario {user_id}")
            
            # Frases por defecto
            default_phrases = [
                "CorpChat", "Gemini", "inteligencia artificial", "IA",
                "Google Cloud", "BigQuery", "Firestore", "Cloud Storage",
                "Vertex AI", "ADK", "multi-agente", "RAG"
            ]
            
            # Agregar frases del contexto si están disponibles
            enhanced_phrases = default_phrases.copy()
            if context_phrases:
                enhanced_phrases.extend(context_phrases)
            
            # Configurar audio
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Detectar formato de audio y configurar encoding apropiado
            audio_info = self.detect_audio_format(audio_content)
            encoding = self._get_audio_encoding(audio_info["format"])
            
            # Configuración con contexto mejorado
            config = speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model="latest_long",
                use_enhanced=True,
                enable_word_confidence=True,
                speech_contexts=[
                    speech.SpeechContext(
                        phrases=enhanced_phrases,
                        boost=15.0  # Boost alto para contexto personalizado
                    )
                ],
                alternative_language_codes=["en-US", "pt-BR"],
                max_alternatives=1,
                profanity_filter=True
            )
            
            # Realizar transcripción
            response = self.client.recognize(config=config, audio=audio)
            
            if not response.results:
                return {
                    "transcript": "",
                    "confidence": 0.0,
                    "language": language_code,
                    "context_enhanced": True,
                    "phrases_used": len(enhanced_phrases),
                    "error": "No se detectó habla en el audio"
                }
            
            result = response.results[0]
            alternative = result.alternatives[0]
            
            return {
                "transcript": alternative.transcript,
                "confidence": alternative.confidence,
                "language": language_code,
                "context_enhanced": True,
                "phrases_used": len(enhanced_phrases),
                "model_used": "latest_long",
                "is_final": True  # Siempre es final para recognize()
            }
            
        except Exception as e:
            _logger.error(f"❌ Error en transcripción con contexto: {e}", exc_info=True)
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": language_code,
                "context_enhanced": True,
                "error": str(e)
            }


class LongDictationProcessor:
    """
    Procesador especializado para dictados largos (hasta 10 minutos).
    Implementa segmentación inteligente y procesamiento optimizado.
    """
    
    def __init__(self):
        self.max_duration = 600  # 10 minutos máximo
        self.optimal_segment_duration = 300  # 5 minutos por segmento
        self.stt_service = STTService()
        
    async def process_long_dictation(
        self, 
        audio_content: bytes, 
        language_code: str = "es-ES"
    ) -> dict:
        """
        Procesa dictados largos usando estrategia optimizada.
        
        Estrategia:
        1. Si ≤ 30s: usar latest_short con recognize()
        2. Si 30s-5min: usar latest_long con recognize()
        3. Si 5-10min: usar latest_long con long_running_recognize()
        4. Si > 10min: rechazar con mensaje claro
        """
        
        estimated_duration = self._estimate_audio_duration(audio_content)
        _logger.info(f"🎤 Procesando dictado largo: {estimated_duration:.1f}s")
        
        if estimated_duration <= 30:
            # Audio muy corto - usar latest_short
            return await self.stt_service.transcribe_audio(
                audio_content, language_code, model="latest_short"
            )
        
        elif estimated_duration <= 300:
            # Audio corto-medio - usar latest_long con recognize()
            return await self.stt_service.transcribe_audio(
                audio_content, language_code, model="latest_long"
            )
        
        elif estimated_duration <= 600:
            # Audio largo - usar latest_long con long_running_recognize()
            return await self.stt_service.transcribe_audio(
                audio_content, language_code, model="latest_long"
            )
        
        else:
            # Audio demasiado largo
            _logger.warning(f"⚠️ Dictado demasiado largo: {estimated_duration:.1f}s")
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": language_code,
                "error": "Audio demasiado largo",
                "message": "El dictado no puede exceder 10 minutos. Por favor, divide tu mensaje en partes más cortas.",
                "max_duration": 600,
                "duration_seconds": estimated_duration,
                "method": "rejected"
            }
    
    def _estimate_audio_duration(self, audio_content: bytes) -> float:
        """
        Estima la duración del audio en segundos.
        Asume formato MP3/WAV con sample rate típico.
        """
        # Estimación básica: 16kHz, 16-bit, mono
        estimated_duration = len(audio_content) / (16000 * 2)
        return estimated_duration
    
    async def get_processing_info(self, audio_content: bytes) -> dict:
        """
        Obtiene información sobre el procesamiento del dictado.
        """
        estimated_duration = self._estimate_audio_duration(audio_content)
        
        if estimated_duration <= 30:
            strategy = "latest_short + recognize()"
            estimated_time = "1-3 segundos"
        elif estimated_duration <= 300:
            strategy = "latest_long + recognize()"
            estimated_time = "3-10 segundos"
        elif estimated_duration <= 600:
            strategy = "latest_long + long_running_recognize()"
            estimated_time = "10-60 segundos"
        else:
            strategy = "rejected (too long)"
            estimated_time = "0 segundos"
        
        return {
            "duration_seconds": estimated_duration,
            "strategy": strategy,
            "estimated_processing_time": estimated_time,
            "can_process": estimated_duration <= 600,
            "max_duration": 600
        }
