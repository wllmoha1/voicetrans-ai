"""
Audio Pipeline Orchestrator.
Coordinates: Raw Audio In -> Whisper STT -> LLM Translation -> Edge-TTS Audio Generation -> Audio Stream Out.
Designed for minimum turnaround time (ultra-low latency).
"""

import time
import asyncio
import logging
from typing import Optional, Dict, Any

from backend.services.stt_service import STTService
from backend.services.translation import TranslationService
from backend.services.tts_service import TTSService
from backend.room_manager import room_manager, Participant

logger = logging.getLogger(__name__)

class AudioPipeline:
    def __init__(self):
        self.stt = STTService()
        self.translator = TranslationService()
        self.tts = TTSService()

    async def process_speech_chunk(
        self,
        room_id: str,
        speaker: Participant,
        audio_bytes: bytes,
        audio_format: str = "webm"
    ):
        """
        Executes the full pipeline for an incoming audio segment from a speaker:
        1. STT: transcribe speaker's audio
        2. Translation: translate to counterpart's selected listening language
        3. TTS: synthesize audio in counterpart's listening language and voice
        4. Transmit: Send synthesized audio to counterpart and broadcast subtitles
        """
        start_time = time.time()
        room = room_manager.get_room(room_id)
        if not room:
            logger.warning(f"Room {room_id} not found during audio processing.")
            return

        counterpart = room.get_counterpart(speaker.session_id)
        if not counterpart:
            logger.info(f"User {speaker.username} spoke, but no counterpart in room {room_id} yet.")
            return

        source_lang = speaker.speaking_language or "so"
        target_lang = counterpart.listening_language or counterpart.speaking_language or "so"
        target_voice_gender = counterpart.voice_gender or "male"

        # Notify participants that AI is processing
        await room_manager.broadcast_json(room_id, {
            "type": "ai_processing",
            "speaker_session_id": speaker.session_id,
            "speaker_id": speaker.user_id,
            "speaker_name": speaker.full_name or speaker.username
        })

        try:
            # Step 1: Speech-to-Text
            t1 = time.time()
            transcribed_text, detected_lang = await self.stt.transcribe_audio(
                audio_bytes=audio_bytes,
                language_code=source_lang,
                file_format=audio_format
            )
            stt_latency = round((time.time() - t1) * 1000, 1)

            if not transcribed_text or not transcribed_text.strip():
                logger.info("STT returned empty text (silence/ambient noise).")
                await room_manager.broadcast_json(room_id, {
                    "type": "ai_idle"
                })
                return

            # Step 2: Translation
            t2 = time.time()
            translated_text = await self.translator.translate_text(
                text=transcribed_text,
                source_lang=source_lang,
                target_lang=target_lang
            )
            translate_latency = round((time.time() - t2) * 1000, 1)

            # Step 3: Text-to-Speech (using crisp brisk delivery rate=+15%)
            t3 = time.time()
            synthesized_audio = await self.tts.synthesize_to_bytes(
                text=translated_text,
                language_code=target_lang,
                gender=target_voice_gender,
                rate="+15%"
            )
            tts_latency = round((time.time() - t3) * 1000, 1)
            total_latency = round((time.time() - start_time) * 1000, 1)

            logger.info(
                f"[Pipeline Latency] Total: {total_latency}ms | "
                f"STT: {stt_latency}ms | Trans: {translate_latency}ms | TTS: {tts_latency}ms"
            )

            # Step 4: Broadcast Translation Subtitles/Event
            subtitle_payload = {
                "type": "translation_complete",
                "speaker_session_id": speaker.session_id,
                "speaker_id": speaker.user_id,
                "speaker_name": speaker.full_name or speaker.username,
                "original_text": transcribed_text,
                "translated_text": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "total_latency_ms": total_latency
            }
            await room_manager.broadcast_json(room_id, subtitle_payload)

            # Step 5: Send the AI Voice Audio directly to the Counterpart's audio player!
            if synthesized_audio and len(synthesized_audio) > 0:
                await counterpart.websocket.send_json({
                    "type": "incoming_audio_start",
                    "text": translated_text,
                    "target_lang": target_lang
                })
                await room_manager.send_audio_bytes(counterpart.websocket, synthesized_audio)

        except Exception as e:
            logger.error(f"Error in Audio Pipeline execution: {e}", exc_info=True)
            await room_manager.broadcast_json(room_id, {
                "type": "ai_error",
                "message": f"Khalad ayaa ka dhacay turjumidda codka: {str(e)}"
            })
        finally:
            await room_manager.broadcast_json(room_id, {
                "type": "ai_idle"
            })


audio_pipeline = AudioPipeline()
