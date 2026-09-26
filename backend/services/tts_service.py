"""
Text-to-Speech (TTS) Service using Microsoft Edge-TTS Neural Voices.
Provides instant, free, ultra-natural neural speech synthesis for Somali, Arabic, English, and all global languages.
"""

import io
import asyncio
import logging
from typing import AsyncGenerator, Optional
import edge_tts

from backend.services.language_catalog import get_voice_for_language

logger = logging.getLogger(__name__)

class TTSService:
    @staticmethod
    async def synthesize_to_bytes(
        text: str, 
        language_code: str, 
        gender: str = "male",
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> bytes:
        """
        Synthesizes text into high-quality MP3 audio bytes using neural voice.
        """
        if not text or not text.strip():
            return b""
            
        voice = get_voice_for_language(language_code, gender)
        logger.info(f"Synthesizing [{language_code} - {voice}]: {text[:50]}...")
        
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            audio_buffer = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.extend(chunk["data"])
            return bytes(audio_buffer)
        except Exception as e:
            logger.error(f"Error in edge-tts synthesis: {e}")
            # Try fallback to English voice if language-specific voice failed
            if voice != "en-US-JennyNeural":
                try:
                    fallback_comm = edge_tts.Communicate(text, "en-US-JennyNeural")
                    audio_buffer = bytearray()
                    async for chunk in fallback_comm.stream():
                        if chunk["type"] == "audio":
                            audio_buffer.extend(chunk["data"])
                    return bytes(audio_buffer)
                except Exception as ex2:
                    logger.error(f"Fallback TTS failed: {ex2}")
            return b""

    @staticmethod
    async def stream_audio_chunks(
        text: str,
        language_code: str,
        gender: str = "male"
    ) -> AsyncGenerator[bytes, None]:
        """
        Streams MP3 audio chunks as they are generated for ultra-low latency playback.
        """
        if not text or not text.strip():
            return
            
        voice = get_voice_for_language(language_code, gender)
        try:
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            logger.error(f"Error streaming TTS: {e}")
