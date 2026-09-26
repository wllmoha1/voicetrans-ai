import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.tts_service import TTSService
from backend.services.language_catalog import get_voice_for_language

async def main():
    print("Testing Somali, Arabic, and English Neural TTS Generation...")

    # Test 1: Somali Male Voice (Muuse)
    somali_text = "Hayye walaal, sidee tahay maanta? Codkan waa AI toos u hadlaya."
    so_voice = get_voice_for_language("so", "male")
    print(f"Testing Somali voice [{so_voice}]...")
    audio_so = await TTSService.synthesize_to_bytes(somali_text, "so", "male")
    print(f"-> Somali Audio generated: {len(audio_so)} bytes")
    assert len(audio_so) > 2000, "Somali TTS audio should be > 2000 bytes"

    # Test 2: English Female Voice (Jenny)
    english_text = "Hello! This is real-time AI voice translation working smoothly."
    en_voice = get_voice_for_language("en", "female")
    print(f"Testing English voice [{en_voice}]...")
    audio_en = await TTSService.synthesize_to_bytes(english_text, "en", "female")
    print(f"-> English Audio generated: {len(audio_en)} bytes")
    assert len(audio_en) > 2000, "English TTS audio should be > 2000 bytes"

    # Test 3: Arabic Male Voice (Hamed)
    arabic_text = "مرحباً بك! هذه ترجمة صوتية فورية بالذكاء الاصطناعي."
    ar_voice = get_voice_for_language("ar", "male")
    print(f"Testing Arabic voice [{ar_voice}]...")
    audio_ar = await TTSService.synthesize_to_bytes(arabic_text, "ar", "male")
    print(f"-> Arabic Audio generated: {len(audio_ar)} bytes")
    assert len(audio_ar) > 2000, "Arabic TTS audio should be > 2000 bytes"

    print("\n ALL TTS TESTS PASSED SUCCESSFULLY! Edge-TTS Somali, English & Arabic voices working perfectly.")

if __name__ == "__main__":
    asyncio.run(main())
