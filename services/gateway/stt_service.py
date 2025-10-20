#!/usr/bin/env python3
"""
Servicio de Speech-to-Text optimizado para CorpChat.
Versión reconstruida desde cero para máxima calidad y robustez.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from google.cloud import speech
import vertexai
from vertexai.language_models import TextEmbeddingModel

_logger = logging.getLogger(__name__)


class STTService:
    """
    Servicio optimizado de Speech-to-Text para CorpChat.
    Características:
    - Alta calidad de transcripción
    - Soporte para audios cortos y largos
    - Configuración optimizada para español
    - Logging detallado de calidad
    - Billing tracking automático
    """

    def __init__(self):
        """Inicializar cliente de Speech-to-Text."""
        try:
            self.client = speech.SpeechClient()
            
            # Labels para billing tracking de CorpChat
            self.billing_labels = {
                "project": "corpchat",
                "billing_project": "corpchat",
                "billing_service": "speech_to_text",
                "billing_team": "corpchat-dev"
            }
            
            _logger.info("✅ Cliente Speech-to-Text inicializado correctamente")
            
        except Exception as e:
            _logger.error(f"❌ Error inicializando Speech-to-Text: {e}", exc_info=True)
            raise

    def detect_audio_format(self, audio_content: bytes) -> Dict[str, Any]:
        """
        Detecta el formato del archivo de audio.
        
        Args:
            audio_content: Contenido binario del archivo de audio
            
        Returns:
            Diccionario con información del formato
        """
        try:
            size_bytes = len(audio_content)
            size_mb = size_bytes / (1024 * 1024)
            
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
                "size_bytes": size_bytes,
                "size_mb": round(size_mb, 2),
                "is_supported": format_type in ["WAV", "MP3", "FLAC", "OGG"]
            }
            
        except Exception as e:
            _logger.error(f"❌ Error detectando formato de audio: {e}")
            return {
                "format": "UNKNOWN",
                "size_bytes": len(audio_content),
                "size_mb": 0,
                "is_supported": False
            }

    def _get_audio_encoding(self, format_type: str) -> speech.RecognitionConfig.AudioEncoding:
        """
        Mapea el formato de audio detectado al encoding de Google Cloud Speech-to-Text.
        
        Args:
            format_type: Tipo de formato detectado
            
        Returns:
            Encoding apropiado para Google Cloud Speech-to-Text
        """
        encoding_map = {
            "WAV": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "MP3": speech.RecognitionConfig.AudioEncoding.MP3,
            "FLAC": speech.RecognitionConfig.AudioEncoding.FLAC,
            "OGG": speech.RecognitionConfig.AudioEncoding.OGG_OPUS
        }
        
        return encoding_map.get(format_type, speech.RecognitionConfig.AudioEncoding.LINEAR16)

    def _estimate_audio_duration(self, audio_content: bytes, format_type: str) -> float:
        """
        Estima la duración del audio en segundos.
        
        Args:
            audio_content: Contenido binario del archivo
            format_type: Tipo de formato del archivo
            
        Returns:
            Duración estimada en segundos
        """
        try:
            if format_type == "MP3":
                # Para MP3: ~128kbps = ~16KB/s
                estimated_duration = len(audio_content) / (128 * 1024 / 8)
            else:
                # Para WAV: 16kHz, 16-bit, mono = 32KB/s
                estimated_duration = len(audio_content) / (16000 * 2)
            
            return max(estimated_duration, 1.0)  # Mínimo 1 segundo
            
        except Exception as e:
            _logger.error(f"❌ Error estimando duración: {e}")
            return 30.0  # Fallback a 30 segundos

    def _create_optimized_config(
        self, 
        encoding: speech.RecognitionConfig.AudioEncoding,
        language_code: str,
        estimated_duration: float
    ) -> speech.RecognitionConfig:
        """
        Crea configuración optimizada para alta calidad de transcripción.
        
        Args:
            encoding: Encoding del audio
            language_code: Código de idioma
            estimated_duration: Duración estimada del audio
            
        Returns:
            Configuración optimizada de reconocimiento
        """
        # Seleccionar modelo basado en duración
        if estimated_duration <= 30:
            model = "latest_short"
        else:
            model = "latest_long"
        
        # Frases de contexto para mejor precisión
        context_phrases = [
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
            "desarrollo", "implementación", "configuración", "deployment",
            "análisis", "datos", "información", "contenido",
            "gestión", "administración", "proceso", "flujo"
        ]
        
        config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=16000,
            language_code=language_code,
            model=model,
            use_enhanced=True,  # Modelo mejorado
            enable_automatic_punctuation=True,  # Puntuación automática
            enable_word_time_offsets=True,  # Timestamps de palabras
            enable_word_confidence=True,  # Confianza por palabra
            speech_contexts=[
                speech.SpeechContext(
                    phrases=context_phrases,
                    boost=20.0  # Boost alto para mejor reconocimiento
                )
            ],
            alternative_language_codes=["en-US", "pt-BR"],
            max_alternatives=1,
            profanity_filter=False  # No filtrar para mantener términos técnicos
        )
        
        return config

    async def transcribe_audio(
        self,
        audio_content: bytes,
        language_code: str = "es-ES",
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = True,
        enable_word_confidence: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio con configuración optimizada para alta calidad.
        
        Args:
            audio_content: Contenido binario del archivo de audio
            language_code: Código de idioma (ej: "es-ES", "en-US")
            enable_automatic_punctuation: Habilitar puntuación automática
            enable_word_time_offsets: Habilitar timestamps de palabras
            enable_word_confidence: Habilitar confianza por palabra
            
        Returns:
            Diccionario con resultado de transcripción
        """
        try:
            _logger.info("🎤 Iniciando transcripción optimizada")
            
            # Detectar formato y estimar duración
            audio_info = self.detect_audio_format(audio_content)
            encoding = self._get_audio_encoding(audio_info["format"])
            estimated_duration = self._estimate_audio_duration(audio_content, audio_info["format"])
            
            _logger.info(f"📊 Audio: {audio_info['format']}, {audio_info['size_mb']:.2f}MB, duración: {estimated_duration:.1f}s")
            
            # Crear configuración optimizada
            config = self._create_optimized_config(encoding, language_code, estimated_duration)
            
            # Configurar audio
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Seleccionar método de reconocimiento
            if estimated_duration <= 60:
                # Audio corto: reconocimiento sincrónico
                _logger.info(f"🔄 Audio corto ({estimated_duration:.1f}s), usando recognize()...")
                response = self.client.recognize(config=config, audio=audio)
                
                if not response.results:
                    _logger.warning("⚠️ No se detectó habla en el audio")
                    return {
                        "transcript": "",
                        "confidence": 0.0,
                        "language": language_code,
                        "words": [],
                        "model_used": config.model,
                        "error": "No se detectó habla en el audio",
                        "method": "recognize",
                        "duration_seconds": estimated_duration
                    }
                
                # Procesar resultado
                result = response.results[0]
                alternative = result.alternatives[0]
                
                # Extraer palabras con timestamps
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
                    "model_used": config.model,
                    "method": "recognize",
                    "duration_seconds": estimated_duration
                }
                
            else:
                # Audio largo: reconocimiento asíncrono
                _logger.info(f"🔄 Audio largo ({estimated_duration:.1f}s), usando long_running_recognize()...")
                operation = self.client.long_running_recognize(config=config, audio=audio)
                
                # Esperar resultado (máximo 5 minutos)
                response = operation.result(timeout=300)
                
                if not response.results:
                    _logger.warning("⚠️ No se detectó habla en el audio (long_running)")
                    return {
                        "transcript": "",
                        "confidence": 0.0,
                        "language": language_code,
                        "words": [],
                        "model_used": config.model,
                        "error": "No se detectó habla en el audio (long_running)",
                        "method": "long_running_recognize",
                        "duration_seconds": estimated_duration
                    }
                
                # Concatenar todos los resultados
                full_transcript = ""
                total_confidence = 0.0
                word_count = 0
                words = []
                
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
                    "model_used": config.model,
                    "method": "long_running_recognize",
                    "duration_seconds": estimated_duration
                }
            
            # Logging de calidad
            quality_level = "Excelente" if transcription_result["confidence"] > 0.9 else "Buena" if transcription_result["confidence"] > 0.7 else "Regular" if transcription_result["confidence"] > 0.5 else "Mala"
            
            _logger.info(
                f"✅ Transcripción completada - Calidad: {transcription_result['confidence']:.2f} ({quality_level})",
                extra={
                    "transcript_length": len(transcription_result["transcript"]),
                    "confidence": transcription_result["confidence"],
                    "quality_level": quality_level,
                    "language": language_code,
                    "model": config.model,
                    "method": transcription_result["method"],
                    "words_count": len(transcription_result["words"]),
                    "duration_seconds": estimated_duration,
                    "transcript_preview": transcription_result["transcript"][:100] + "..." if len(transcription_result["transcript"]) > 100 else transcription_result["transcript"],
                    **self.billing_labels
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
                "model_used": "error",
                "error": str(e),
                "method": "failed"
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
            "es-PE": "Español (Perú)",
            "es-VE": "Español (Venezuela)",
            "es-CL": "Español (Chile)",
            "es-UY": "Español (Uruguay)",
            "es-PY": "Español (Paraguay)",
            "es-BO": "Español (Bolivia)",
            "es-EC": "Español (Ecuador)",
            "es-CR": "Español (Costa Rica)",
            "es-PA": "Español (Panamá)",
            "es-GT": "Español (Guatemala)",
            "es-HN": "Español (Honduras)",
            "es-SV": "Español (El Salvador)",
            "es-NI": "Español (Nicaragua)",
            "es-DO": "Español (República Dominicana)",
            "es-CU": "Español (Cuba)",
            "es-PR": "Español (Puerto Rico)",
            "en-US": "Inglés (Estados Unidos)",
            "en-GB": "Inglés (Reino Unido)",
            "en-AU": "Inglés (Australia)",
            "en-CA": "Inglés (Canadá)",
            "pt-BR": "Portugués (Brasil)",
            "pt-PT": "Portugués (Portugal)",
            "fr-FR": "Francés (Francia)",
            "de-DE": "Alemán (Alemania)",
            "it-IT": "Italiano (Italia)",
            "ja-JP": "Japonés (Japón)",
            "ko-KR": "Coreano (Corea del Sur)",
            "zh-CN": "Chino (China)",
            "zh-TW": "Chino (Taiwán)",
            "ru-RU": "Ruso (Rusia)",
            "ar-SA": "Árabe (Arabia Saudí)",
            "hi-IN": "Hindi (India)"
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
    ) -> Dict[str, Any]:
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
                audio_content, language_code
            )
        
        elif estimated_duration <= 300:
            # Audio corto-medio - usar latest_long con recognize()
            return await self.stt_service.transcribe_audio(
                audio_content, language_code
            )
        
        elif estimated_duration <= 600:
            # Audio largo - usar latest_long con long_running_recognize()
            return await self.stt_service.transcribe_audio(
                audio_content, language_code
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

    async def get_processing_info(self, audio_content: bytes) -> Dict[str, Any]:
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
