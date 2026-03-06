# Lazy import lingua
import logging

logger = logging.getLogger(__name__)

# Build detector once (supports all languages)
_detector = None


def _get_detector():
    global _detector
    if _detector is None:
        logger.info("Building language detector...")
        from lingua import LanguageDetectorBuilder
        _detector = LanguageDetectorBuilder.from_all_languages().build()
        logger.info("Language detector ready.")
    return _detector


# Mapping of lingua Language name to ISO codes and names
_LANG_MAP = {
    "ENGLISH": ("en", "English"),
    "HINDI": ("hi", "Hindi"),
    "FRENCH": ("fr", "French"),
    "GERMAN": ("de", "German"),
    "SPANISH": ("es", "Spanish"),
    "PORTUGUESE": ("pt", "Portuguese"),
    "ITALIAN": ("it", "Italian"),
    "DUTCH": ("nl", "Dutch"),
    "RUSSIAN": ("ru", "Russian"),
    "CHINESE": ("zh", "Chinese"),
    "JAPANESE": ("ja", "Japanese"),
    "KOREAN": ("ko", "Korean"),
    "ARABIC": ("ar", "Arabic"),
    "TURKISH": ("tr", "Turkish"),
    "BENGALI": ("bn", "Bengali"),
    "TAMIL": ("ta", "Tamil"),
    "TELUGU": ("te", "Telugu"),
    "MARATHI": ("mr", "Marathi"),
    "GUJARATI": ("gu", "Gujarati"),
    "PUNJABI": ("pa", "Punjabi"),
    "URDU": ("ur", "Urdu"),
    "THAI": ("th", "Thai"),
    "VIETNAMESE": ("vi", "Vietnamese"),
    "INDONESIAN": ("id", "Indonesian"),
    "MALAY": ("ms", "Malay"),
    "POLISH": ("pl", "Polish"),
    "UKRAINIAN": ("uk", "Ukrainian"),
    "CZECH": ("cs", "Czech"),
    "SWEDISH": ("sv", "Swedish"),
    "DANISH": ("da", "Danish"),
    "BOKMAL": ("nb", "Norwegian"),
    "FINNISH": ("fi", "Finnish"),
    "HUNGARIAN": ("hu", "Hungarian"),
    "ROMANIAN": ("ro", "Romanian"),
    "GREEK": ("el", "Greek"),
    "HEBREW": ("he", "Hebrew"),
    "PERSIAN": ("fa", "Persian"),
    "CATALAN": ("ca", "Catalan"),
}

# Indian language ISO codes
INDIAN_LANGUAGES = {"hi", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "ur", "as", "or", "sa", "ne", "sd", "ks", "doi", "kok", "mai", "mni", "sat", "bo"}


def detect_language(text: str) -> dict:
    """Detect the language of the given text."""
    detector = _get_detector()

    try:
        # Use confidence-based detection
        confidence_values = detector.compute_language_confidence_values(text[:2000])

        if confidence_values:
            top = confidence_values[0]
            lang = top.language
            confidence = top.value

            if lang.name in _LANG_MAP:
                code, name = _LANG_MAP[lang.name]
            else:
                code = lang.name.lower()[:2]
                name = lang.name.title()

            return {
                "detected_language": name,
                "language_code": code,
                "confidence": round(confidence, 4),
                "is_english": code == "en",
                "is_indian": code in INDIAN_LANGUAGES,
            }
    except Exception as e:
        logger.error(f"Language detection failed: {e}")

    return {
        "detected_language": "English",
        "language_code": "en",
        "confidence": 0.0,
        "is_english": True,
        "is_indian": False,
    }
