import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.language_catalog import LANGUAGES, get_voice_for_language, get_language_name
from backend.services.translation import TranslationService

async def test_pipeline():
    print("Testing Language Catalog and Translation Service...")

    # Test 1: Language Catalog validation
    assert len(LANGUAGES) >= 20, "Catalog should have at least 20 languages"
    assert "so" in LANGUAGES, "Somali ('so') must be in catalog"
    assert "ar" in LANGUAGES, "Arabic ('ar') must be in catalog"
    assert "en" in LANGUAGES, "English ('en') must be in catalog"

    so_voice_male = get_voice_for_language("so", "male")
    so_voice_female = get_voice_for_language("so", "female")
    assert so_voice_male == "so-SO-MuuseNeural"
    assert so_voice_female == "so-SO-UbaxNeural"
    print(f"-> Somali Neural Voices verified: Male={so_voice_male}, Female={so_voice_female}")

    # Test 2: Translation Service
    translator = TranslationService()
    
    # Test conversational fallback phrase
    phrase_so = "Sidee tahay walaal?"
    translated_en = await translator.translate_text(phrase_so, "so", "en")
    print(f"-> Translation [so -> en]: '{phrase_so}' => '{translated_en}'")
    assert len(translated_en) > 0, "Translation result must not be empty"

    phrase_en = "Hello! How are you doing?"
    translated_so = await translator.translate_text(phrase_en, "en", "so")
    print(f"-> Translation [en -> so]: '{phrase_en}' => '{translated_so}'")
    assert len(translated_so) > 0, "Translation result must not be empty"

    print("\n ALL PIPELINE & CATALOG TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
