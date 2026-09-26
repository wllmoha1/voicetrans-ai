"""
Ultra-fast real-time speech translation service.
Uses Groq Llama 3.3 70B (or Gemini API) for conversational speech translation.
"""

import os
import logging
from typing import Optional
from groq import AsyncGroq
from backend.config import GROQ_API_KEY, GEMINI_API_KEY
from backend.services.language_catalog import get_language_name

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.groq_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

    async def translate_text(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> str:
        """
        Translates conversational speech text from source_lang to target_lang.
        Designed specifically for natural conversational tone in voice calls.
        """
        if not text or not text.strip():
            return ""
            
        # If source and target are the same language, no translation needed
        if source_lang.split("-")[0].lower() == target_lang.split("-")[0].lower():
            return text.strip()

        source_name = get_language_name(source_lang)
        target_name = get_language_name(target_lang)

        # 1. Try Groq Llama-3.3-70b (sub-150ms latency)
        if self.groq_client:
            try:
                system_prompt = (
                    f"You are a real-time simultaneous voice call translator. "
                    f"Translate the following spoken sentence from {source_name} to {target_name}. "
                    f"Rules:\n"
                    f"1. Produce ONLY the translated sentence that will be spoken aloud by text-to-speech.\n"
                    f"2. Keep the natural, friendly, conversational spoken tone.\n"
                    f"3. Do NOT add any explanations, brackets, notes, or punctuation artifacts.\n"
                    f"4. If translating between Somali and English/Arabic/others, ensure authentic idiomatic phrasing."
                )

                models_to_try = ["llama-3.1-8b-instant", "llama3-8b-8192", "llama-3.3-70b-versatile"]
                response = None
                for m in models_to_try:
                    try:
                        response = await self.groq_client.chat.completions.create(
                            model=m,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": text.strip()}
                            ],
                            temperature=0.3,
                            max_tokens=256
                        )
                        break
                    except Exception as me:
                        logger.warning(f"Groq model {m} failed: {me}. Trying next...")
                
                if response:
                    translated = response.choices[0].message.content.strip()
                    translated = translated.strip('"\'`')
                    logger.info(f"Translated [{source_lang} -> {target_lang}]: '{text}' => '{translated}'")
                    return translated
            except Exception as e:
                logger.error(f"Groq translation error: {e}")

        # 2. Fallback / Mock translation if no API key is provided
        logger.warning("No Groq API key configured or request failed. Using fallback translation.")
        return self._simple_fallback_translate(text, source_lang, target_lang)

    def _simple_fallback_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Simple dictionary and placeholder fallback so system functions even without external API keys during dev/testing.
        """
        sample_dict = {
            ("so", "en"): {
                "iska warran": "How are you?",
                "sideed tahay": "How are you doing?",
                "sidee tahay": "How are you?",
                "subax wanaagsan": "Good morning!",
                "galab wanaagsan": "Good afternoon!",
                "habeen wanaagsan": "Good evening!",
                "mahadsanid": "Thank you very much!",
                "waan fiicanahay": "I am doing well.",
                "haye": "Alright!",
                "nabad gelyo": "Goodbye!",
                "magacaa": "What is your name?",
                "haa": "Yes",
                "maya": "No"
            },
            ("en", "so"): {
                "hello": "Hayye, asalaamu calaykum!",
                "hi": "Asc!",
                "how are you": "Sidee tahay walaal?",
                "how are you doing": "Sidee tahay?",
                "i am doing well": "Aad baan u fiicanahay, mahadsanid.",
                "i am fine": "Waan fiicanahay.",
                "good morning": "Subax wanaagsan!",
                "good afternoon": "Galab wanaagsan!",
                "good evening": "Habeen wanaagsan!",
                "thank you": "Aad baad u mahadsantahay!",
                "yes": "Haa",
                "no": "Maya",
                "goodbye": "Nabad gelyo!",
                "bye": "Nabadeey!"
            }
        }
        
        src_key = source_lang.split("-")[0].lower()
        tgt_key = target_lang.split("-")[0].lower()
        
        text_lower = text.lower().strip(" .!?,")
        pair = sample_dict.get((src_key, tgt_key), {})
        for phrase, translation in pair.items():
            if phrase in text_lower:
                return translation
                
        # If not in sample dictionary, return text with target notification
        return f"[{get_language_name(target_lang)}]: {text}"
