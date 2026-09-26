"""
Speech-to-Text (STT) Service using Groq Whisper Large-v3.
Handles ultra-low latency transcription for Somali, Arabic, English, and all global languages.
"""

import io
import logging
from typing import Optional, Tuple
from groq import AsyncGroq
from backend.config import GROQ_API_KEY

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self):
        self.groq_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language_code: Optional[str] = None,
        file_format: str = "webm"
    ) -> Tuple[str, str]:
        """
        Transcribes raw audio bytes into text using Whisper Large v3.
        Returns a tuple of (transcribed_text, detected_language).
        """
        if not audio_bytes or len(audio_bytes) < 100:
            return "", language_code or "en"

        if not self.groq_client:
            logger.warning("GROQ_API_KEY is not configured! STT cannot call Whisper API.")
            return "", language_code or "en"

        filename = f"audio_chunk.{file_format}"
        file_obj = (filename, audio_bytes)
        
        # Format language for Whisper (2-letter ISO code e.g. 'so', 'en', 'ar')
        lang = language_code.split("-")[0].lower() if language_code else None

        try:
            params = {
                "file": file_obj,
                "model": "whisper-large-v3",
                "response_format": "verbose_json",
                "temperature": 0.0
            }
            if lang and lang != "auto":
                params["language"] = lang

            response = await self.groq_client.audio.transcriptions.create(**params)
            
            text = response.text.strip() if hasattr(response, "text") else str(response).strip()
            detected_lang = getattr(response, "language", lang or "en")
            
            logger.info(f"Transcribed ({detected_lang}): '{text}'")
            return text, detected_lang
        except Exception as e:
            logger.error(f"Error in Groq Whisper transcription: {e}")
            return "", language_code or "en"
