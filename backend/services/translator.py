"""
Translation service:
  - IndicTrans2 (local model) for Indian languages  <->  English
  - Groq API (llama-3.1-8b-instant) fallback for non-Indian languages
"""

import requests
import logging
import torch
import nltk
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Groq config (fallback for non-Indian languages)
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

# ---------------------------------------------------------------------------
# Language metadata
# ---------------------------------------------------------------------------
LANG_NAMES = {
    "fr": "French", "de": "German", "es": "Spanish", "pt": "Portuguese",
    "it": "Italian", "nl": "Dutch", "ru": "Russian", "zh": "Chinese",
    "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "tr": "Turkish",
    "th": "Thai", "vi": "Vietnamese", "id": "Indonesian", "ms": "Malay",
    "pl": "Polish", "uk": "Ukrainian", "cs": "Czech", "sv": "Swedish",
    "da": "Danish", "nb": "Norwegian", "fi": "Finnish", "hu": "Hungarian",
    "ro": "Romanian", "el": "Greek", "he": "Hebrew", "fa": "Persian",
    "ca": "Catalan",
    "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
    "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam",
    "pa": "Punjabi", "ur": "Urdu", "ne": "Nepali", "as": "Assamese",
    "or": "Odia", "sd": "Sindhi", "sa": "Sanskrit",
}

INDIAN_LANGS = {
    "hi", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "ur",
    "as", "or", "ne", "sd", "sa", "mai", "kok", "doi", "mni", "sat", "ks",
}

# ---------------------------------------------------------------------------
# IndicTrans2 — ISO 639-1  →  flores-200 code mapping
# ---------------------------------------------------------------------------
_ISO_TO_FLORES: dict[str, str] = {
    "hi": "hin_Deva",
    "bn": "ben_Beng",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "mr": "mar_Deva",
    "gu": "guj_Gujr",
    "kn": "kan_Knda",
    "ml": "mal_Mlym",
    "pa": "pan_Guru",
    "ur": "urd_Arab",
    "ne": "npi_Deva",
    "as": "asm_Beng",
    "or": "ory_Orya",
    "sd": "snd_Arab",
    "sa": "san_Deva",
    "mai": "mai_Deva",
    "kok": "gom_Deva",
    "doi": "doi_Deva",
    "mni": "mni_Mtei",
    "sat": "sat_Olck",
    "ks": "kas_Arab",
}

_FLORES_ENG = "eng_Latn"

# ---------------------------------------------------------------------------
# Gemini API core translation (replacing IndicTrans2)
# ---------------------------------------------------------------------------
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
_gemini_model = "gemini-1.5-flash"

def _gemini_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using Gemini API."""
    try:
        model = genai.GenerativeModel(_gemini_model)
        prompt = f"You are a professional translator. Translate the following {source_lang} text to {target_lang}. Preserve the meaning, tone, and factual content accurately. Return ONLY the {target_lang} translation, nothing else.\n\nText:\n{text}"
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
            )
        )
        return response.text.strip() or text
    except Exception as e:
        logger.error(f"Gemini translation failed: {e}")
        return text

def _indictrans_translate_long(text: str, src_lang: str, tgt_lang: str, direction: str) -> str:
    """Wrapper to use Gemini instead of IndicTrans2 for Indian languages."""
    # Convert flores-200 code back to human-readable language
    reverse_flores = {v: k for k, v in _ISO_TO_FLORES.items()}
    
    if direction == "indic2en":
        iso_code = reverse_flores.get(src_lang, "Hindi")
        human_lang = LANG_NAMES.get(iso_code, "Indian Language")
        return _gemini_translate(text, human_lang, "English")
    else:
        iso_code = reverse_flores.get(tgt_lang, "Hindi")
        human_lang = LANG_NAMES.get(iso_code, "Indian Language")
        return _gemini_translate(text, "English", human_lang)



# ---------------------------------------------------------------------------
# Groq API (fallback for non-Indian languages)
# ---------------------------------------------------------------------------

def _groq_translate(text: str, source_lang: str) -> str:
    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": f"You are a professional translator. Translate the following {source_lang} text to English. Preserve the meaning, tone, and factual content accurately. Return ONLY the English translation, nothing else."},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.1,
                "max_tokens": 4000,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            logger.error(f"Groq returned empty choices: {data}")
            return text
        return choices[0].get("message", {}).get("content", text).strip() or text
    except Exception as e:
        logger.error(f"Groq translation failed: {e}")
        return text


def _groq_translate_to_target(text: str, target_lang: str) -> str:
    """Translate English text to a non-Indian target language via Groq."""
    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": f"Translate the following English text to {target_lang}. Keep the same structure and formatting. Return ONLY the translation."},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.1,
                "max_tokens": 4000,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            logger.error("Groq output translation returned empty choices")
            return text
        return choices[0].get("message", {}).get("content", text).strip() or text
    except Exception as e:
        logger.error(f"Output translation to {target_lang} failed: {e}")
        return text


def _chunk_for_groq(text: str, max_words: int = 1500) -> list[str]:
    sentences = text.replace("\n", " ").split(". ")
    chunks, current_chunk, current_len = [], [], 0
    for sent in sentences:
        sent_len = len(sent.split())
        if current_len + sent_len > max_words and current_chunk:
            chunks.append(". ".join(current_chunk) + ".")
            current_chunk, current_len = [sent], sent_len
        else:
            current_chunk.append(sent)
            current_len += sent_len
    if current_chunk:
        chunks.append(". ".join(current_chunk))
    return chunks if chunks else [text]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate_to_english(text: str, source_lang_code: str) -> str:
    """Translate input text to English.

    Uses IndicTrans2 for Indian languages, Groq API for others.
    """
    if source_lang_code == "en":
        return text

    flores_code = _ISO_TO_FLORES.get(source_lang_code)
    if flores_code:
        # Indian language → use IndicTrans2 locally
        logger.info(f"Using IndicTrans2 for {source_lang_code} ({flores_code}) → English")
        try:
            return _indictrans_translate_long(text, flores_code, _FLORES_ENG, "indic2en")
        except Exception as e:
            logger.error(f"IndicTrans2 indic→en failed, falling back to Groq: {e}")
            # Fall through to Groq

    # Non-Indian language or IndicTrans2 failure → Groq
    lang_name = LANG_NAMES.get(source_lang_code, source_lang_code)
    logger.info(f"Using Groq API for {lang_name} → English translation")
    chunks = _chunk_for_groq(text, max_words=1500)
    parts = [_groq_translate(chunk, lang_name) for chunk in chunks]
    return " ".join(parts)


def translate_output(text: str, target_lang_code: str) -> str:
    """Translate output text (summary/rewrites) from English to a target language.

    Uses IndicTrans2 for Indian languages, Groq API for others.
    """
    if target_lang_code == "en":
        return text

    flores_code = _ISO_TO_FLORES.get(target_lang_code)
    if flores_code:
        # English → Indian language via IndicTrans2
        logger.info(f"Using IndicTrans2 for English → {target_lang_code} ({flores_code})")
        try:
            return _indictrans_translate_long(text, _FLORES_ENG, flores_code, "en2indic")
        except Exception as e:
            logger.error(f"IndicTrans2 en→indic failed, falling back to Groq: {e}")

    # Non-Indian or fallback → Groq
    lang_name = LANG_NAMES.get(target_lang_code, target_lang_code)
    logger.info(f"Using Groq API for English → {lang_name} output translation")
    return _groq_translate_to_target(text, lang_name)


def translate_output_batch(texts: list[str], target_lang_code: str) -> list[str]:
    """Translate multiple output texts from English to a target language in one shot.
    """
    if target_lang_code == "en" or not texts:
        return texts

    flores_code = _ISO_TO_FLORES.get(target_lang_code)
    if flores_code:
        logger.info(f"Translating {len(texts)} texts via Gemini → {target_lang_code}")
        reverse_flores = {v: k for k, v in _ISO_TO_FLORES.items()}
        iso_code = reverse_flores.get(flores_code, "Hindi")
        human_lang = LANG_NAMES.get(iso_code, "Indian Language")
        
        return [_gemini_translate(t, "English", human_lang) for t in texts]

    # Fallback: Groq API for all texts
    lang_name = LANG_NAMES.get(target_lang_code, target_lang_code)
    logger.info(f"Falling back to Groq API for {len(texts)} texts → {lang_name}")
    return [_groq_translate_to_target(t, lang_name) for t in texts]


def get_translation_method(source_lang_code: str) -> str:
    """Return which translation backend is used for the given language."""
    if source_lang_code == "en":
        return "none"
    if source_lang_code in _ISO_TO_FLORES:
        return "gemini"
    return "groq"


def is_indian_language(code: str) -> bool:
    return code in INDIAN_LANGS


def unload_translation_model():
    """Unload models to free GPU memory (no-op now that Gemini is used)."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Translation models unloaded (no-op for Gemini).")
