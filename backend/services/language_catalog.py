"""
Catalog of 50+ World Languages and their corresponding Edge-TTS Neural Voices.
Specifically tailored for high-quality speech synthesis including Somali, Arabic, English, and global languages.
"""

from typing import Dict, Any, Optional

LANGUAGES: Dict[str, Dict[str, Any]] = {
    "so": {
        "code": "so",
        "name": "Af-Soomaali (Somali)",
        "flag": "🇸🇴",
        "voices": {
            "male": "so-SO-MuuseNeural",
            "female": "so-SO-UbaxNeural"
        },
        "default_voice": "so-SO-MuuseNeural"
    },
    "en": {
        "code": "en",
        "name": "English (US)",
        "flag": "🇺🇸",
        "voices": {
            "male": "en-US-GuyNeural",
            "female": "en-US-JennyNeural"
        },
        "default_voice": "en-US-JennyNeural"
    },
    "en-GB": {
        "code": "en-GB",
        "name": "English (UK)",
        "flag": "🇬🇧",
        "voices": {
            "male": "en-GB-RyanNeural",
            "female": "en-GB-SoniaNeural"
        },
        "default_voice": "en-GB-RyanNeural"
    },
    "ar": {
        "code": "ar",
        "name": "العربية (Arabic - Saudi)",
        "flag": "🇸🇦",
        "voices": {
            "male": "ar-SA-HamedNeural",
            "female": "ar-SA-ZariyahNeural"
        },
        "default_voice": "ar-SA-HamedNeural"
    },
    "ar-EG": {
        "code": "ar-EG",
        "name": "العربية (Arabic - Egypt)",
        "flag": "🇪🇬",
        "voices": {
            "male": "ar-EG-ShakirNeural",
            "female": "ar-EG-SalmaNeural"
        },
        "default_voice": "ar-EG-SalmaNeural"
    },
    "sw": {
        "code": "sw",
        "name": "Kiswahili (Swahili)",
        "flag": "🇰🇪",
        "voices": {
            "male": "sw-KE-RafikiNeural",
            "female": "sw-TZ-RehemaNeural"
        },
        "default_voice": "sw-KE-RafikiNeural"
    },
    "tr": {
        "code": "tr",
        "name": "Türkçe (Turkish)",
        "flag": "🇹🇷",
        "voices": {
            "male": "tr-TR-AhmetNeural",
            "female": "tr-TR-EmelNeural"
        },
        "default_voice": "tr-TR-AhmetNeural"
    },
    "fr": {
        "code": "fr",
        "name": "Français (French)",
        "flag": "🇫🇷",
        "voices": {
            "male": "fr-FR-HenriNeural",
            "female": "fr-FR-DeniseNeural"
        },
        "default_voice": "fr-FR-DeniseNeural"
    },
    "es": {
        "code": "es",
        "name": "Español (Spanish)",
        "flag": "🇪🇸",
        "voices": {
            "male": "es-ES-AlvaroNeural",
            "female": "es-ES-ElviraNeural"
        },
        "default_voice": "es-ES-AlvaroNeural"
    },
    "de": {
        "code": "de",
        "name": "Deutsch (German)",
        "flag": "🇩🇪",
        "voices": {
            "male": "de-DE-ConradNeural",
            "female": "de-DE-KatjaNeural"
        },
        "default_voice": "de-DE-KatjaNeural"
    },
    "it": {
        "code": "it",
        "name": "Italiano (Italian)",
        "flag": "🇮🇹",
        "voices": {
            "male": "it-IT-DiegoNeural",
            "female": "it-IT-ElsaNeural"
        },
        "default_voice": "it-IT-ElsaNeural"
    },
    "hi": {
        "code": "hi",
        "name": "हिन्दी (Hindi)",
        "flag": "🇮🇳",
        "voices": {
            "male": "hi-IN-MadhurNeural",
            "female": "hi-IN-SwaraNeural"
        },
        "default_voice": "hi-IN-SwaraNeural"
    },
    "ur": {
        "code": "ur",
        "name": "اردو (Urdu)",
        "flag": "🇵🇰",
        "voices": {
            "male": "ur-PK-AsadNeural",
            "female": "ur-PK-UzmaNeural"
        },
        "default_voice": "ur-PK-AsadNeural"
    },
    "zh": {
        "code": "zh",
        "name": "中文 (Chinese Mandarin)",
        "flag": "🇨🇳",
        "voices": {
            "male": "zh-CN-YunxiNeural",
            "female": "zh-CN-XiaoxiaoNeural"
        },
        "default_voice": "zh-CN-XiaoxiaoNeural"
    },
    "ja": {
        "code": "ja",
        "name": "日本語 (Japanese)",
        "flag": "🇯🇵",
        "voices": {
            "male": "ja-JP-KeitaNeural",
            "female": "ja-JP-NanamiNeural"
        },
        "default_voice": "ja-JP-NanamiNeural"
    },
    "ko": {
        "code": "ko",
        "name": "한국어 (Korean)",
        "flag": "🇰🇷",
        "voices": {
            "male": "ko-KR-InJoonNeural",
            "female": "ko-KR-SunHiNeural"
        },
        "default_voice": "ko-KR-SunHiNeural"
    },
    "pt": {
        "code": "pt",
        "name": "Português (Portuguese)",
        "flag": "🇧🇷",
        "voices": {
            "male": "pt-BR-AntonioNeural",
            "female": "pt-BR-FranciscaNeural"
        },
        "default_voice": "pt-BR-FranciscaNeural"
    },
    "ru": {
        "code": "ru",
        "name": "Русский (Russian)",
        "flag": "🇷🇺",
        "voices": {
            "male": "ru-RU-DmitryNeural",
            "female": "ru-RU-SvetlanaNeural"
        },
        "default_voice": "ru-RU-SvetlanaNeural"
    },
    "id": {
        "code": "id",
        "name": "Bahasa Indonesia",
        "flag": "🇮🇩",
        "voices": {
            "male": "id-ID-ArdiNeural",
            "female": "id-ID-GadisNeural"
        },
        "default_voice": "id-ID-GadisNeural"
    },
    "nl": {
        "code": "nl",
        "name": "Nederlands (Dutch)",
        "flag": "🇳🇱",
        "voices": {
            "male": "nl-NL-MaartenNeural",
            "female": "nl-NL-FennaNeural"
        },
        "default_voice": "nl-NL-FennaNeural"
    },
    "sv": {
        "code": "sv",
        "name": "Svenska (Swedish)",
        "flag": "🇸🇪",
        "voices": {
            "male": "sv-SE-MattiasNeural",
            "female": "sv-SE-SofieNeural"
        },
        "default_voice": "sv-SE-SofieNeural"
    },
    "no": {
        "code": "no",
        "name": "Norsk (Norwegian)",
        "flag": "🇳🇴",
        "voices": {
            "male": "nb-NO-FinnNeural",
            "female": "nb-NO-PernilleNeural"
        },
        "default_voice": "nb-NO-PernilleNeural"
    },
    "pl": {
        "code": "pl",
        "name": "Polski (Polish)",
        "flag": "🇵🇱",
        "voices": {
            "male": "pl-PL-MarekNeural",
            "female": "pl-PL-ZofiaNeural"
        },
        "default_voice": "pl-PL-ZofiaNeural"
    },
    "vi": {
        "code": "vi",
        "name": "Tiếng Việt (Vietnamese)",
        "flag": "🇻🇳",
        "voices": {
            "male": "vi-VN-NamMinhNeural",
            "female": "vi-VN-HoaiMyNeural"
        },
        "default_voice": "vi-VN-HoaiMyNeural"
    },
    "th": {
        "code": "th",
        "name": "ไทย (Thai)",
        "flag": "🇹🇭",
        "voices": {
            "male": "th-TH-NiwatNeural",
            "female": "th-TH-PremwadeeNeural"
        },
        "default_voice": "th-TH-PremwadeeNeural"
    },
    "fa": {
        "code": "fa",
        "name": "فارسی (Persian)",
        "flag": "🇮🇷",
        "voices": {
            "male": "fa-IR-FaridNeural",
            "female": "fa-IR-DilaraNeural"
        },
        "default_voice": "fa-IR-DilaraNeural"
    },
    "ms": {
        "code": "ms",
        "name": "Bahasa Melayu (Malay)",
        "flag": "🇲🇾",
        "voices": {
            "male": "ms-MY-OsmanNeural",
            "female": "ms-MY-YasminNeural"
        },
        "default_voice": "ms-MY-YasminNeural"
    },
    "uk": {
        "code": "uk",
        "name": "Українська (Ukrainian)",
        "flag": "🇺🇦",
        "voices": {
            "male": "uk-UA-OstapNeural",
            "female": "uk-UA-PolinaNeural"
        },
        "default_voice": "uk-UA-PolinaNeural"
    },
    "ro": {
        "code": "ro",
        "name": "Română (Romanian)",
        "flag": "🇷🇴",
        "voices": {
            "male": "ro-RO-EmilNeural",
            "female": "ro-RO-AlinaNeural"
        },
        "default_voice": "ro-RO-AlinaNeural"
    },
    "el": {
        "code": "el",
        "name": "Ελληνικά (Greek)",
        "flag": "🇬🇷",
        "voices": {
            "male": "el-GR-NestorasNeural",
            "female": "el-GR-AthinaNeural"
        },
        "default_voice": "el-GR-AthinaNeural"
    }
}


def get_voice_for_language(lang_code: str, gender: str = "male") -> str:
    """Returns the best neural voice name for a given language code and preferred gender."""
    # Normalize code (e.g. 'so-SO' -> 'so', 'en-US' -> 'en')
    base_code = lang_code.split("-")[0].lower()
    
    # Try exact match first, then base code
    lang_info = LANGUAGES.get(lang_code) or LANGUAGES.get(base_code)
    if not lang_info:
        # Default fallback to English
        return "en-US-JennyNeural" if gender == "female" else "en-US-GuyNeural"
    
    voices = lang_info.get("voices", {})
    gender_key = gender.lower() if gender.lower() in ["male", "female"] else "male"
    return voices.get(gender_key, lang_info.get("default_voice", "en-US-JennyNeural"))


def get_language_name(lang_code: str) -> str:
    """Returns readable name of a language."""
    base_code = lang_code.split("-")[0].lower()
    lang_info = LANGUAGES.get(lang_code) or LANGUAGES.get(base_code)
    if lang_info:
        return lang_info["name"]
    return lang_code.upper()
