from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import logging
import nltk
import json
import time
import requests
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

logger = logging.getLogger(__name__)

# punkt_tab already extracted locally

# Global model holders
_bias_classifier = None
_political_classifier = None

# Groq API config (same key as summarizer)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

# Retry settings for Groq 429 errors
_MAX_RETRIES = 5
_BASE_DELAY = 2  # seconds


def _get_bias_classifier():
    global _bias_classifier
    if _bias_classifier is None:
        logger.info("Loading bias type classifier...")
        device = 0 if torch.cuda.is_available() else -1
        _bias_classifier = pipeline(
            "text-classification",
            model="cirimus/modernbert-large-bias-type-classifier",
            top_k=None,
            device=device,
            truncation=True,
            max_length=512,
            model_kwargs={"low_cpu_mem_usage": True, "torch_dtype": torch.float16},
        )
        logger.info("Bias classifier loaded.")
    return _bias_classifier


# Maps LABEL_N → human-readable political leaning
_POLITICAL_LABEL_MAP = {
    "label_0": "left",
    "label_1": "center",
    "label_2": "right",
    # Already-named variants (older transformers)
    "left": "left",
    "center": "center",
    "right": "right",
}


def _get_political_classifier():
    global _political_classifier
    if _political_classifier is None:
        logger.info("Loading political leaning classifier...")
        device = 0 if torch.cuda.is_available() else -1
        _political_classifier = pipeline(
            "text-classification",
            model="matous-volf/political-leaning-politics",
            top_k=None,
            device=device,
            truncation=True,
            max_length=512,
            model_kwargs={"low_cpu_mem_usage": True, "torch_dtype": torch.float16},
        )
        logger.info("Political classifier loaded.")
    return _political_classifier


def classify_bias_types(text: str) -> list[dict]:
    """Classify article text for bias types. Returns list of {bias_type, confidence}."""
    classifier = _get_bias_classifier()

    # Chunk text into ~512 token segments
    chunks = _chunk_text(text, max_words=400)
    aggregated = {}

    for chunk in chunks:
        try:
            results = classifier(chunk)
            if results and isinstance(results[0], list):
                results = results[0]
            for r in results:
                label = r["label"]
                score = r["score"]
                if label in aggregated:
                    aggregated[label] = max(aggregated[label], score)
                else:
                    aggregated[label] = score
        except Exception as e:
            logger.warning(f"Bias classification chunk failed: {e}")
            continue

    # Sort by confidence, return top results
    sorted_results = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)
    return [{"bias_type": label, "confidence": round(score, 4)} for label, score in sorted_results]


def classify_political_leaning(text: str) -> dict:
    """Classify political leaning using Groq first (globally aware), with HuggingFace model as fallback."""
    
    # Try Groq first (more accurate for global politics)
    groq_result = _groq_political_leaning(text)
    if groq_result:
        logger.info(f"Political leaning (Groq): {groq_result['label']} ({groq_result['confidence']})")
        return groq_result

    # Fallback to HuggingFace model
    classifier = _get_political_classifier()

    chunks = _chunk_text(text, max_words=400)
    aggregated = {}

    for chunk in chunks:
        try:
            results = classifier(chunk)
            if results and isinstance(results[0], list):
                results = results[0]
            for r in results:
                raw_label = r["label"].lower()
                label = _POLITICAL_LABEL_MAP.get(raw_label, raw_label)
                score = r["score"]
                if label in aggregated:
                    aggregated[label] = max(aggregated[label], score)
                else:
                    aggregated[label] = score
        except Exception as e:
            logger.warning(f"Political classification chunk failed: {e}")
            continue

    if not aggregated:
        return {"label": "center", "confidence": 0.0}

    best = max(aggregated.items(), key=lambda x: x[1])
    return {"label": best[0], "confidence": round(best[1], 4)}


def _groq_political_leaning(text: str) -> Optional[dict]:
    """Use Groq LLM to classify political leaning — works for global politics, not just US."""
    words = text.split()
    if len(words) > 2000:
        text = " ".join(words[:2000])

    prompt = """Analyze this news article's political leaning. Consider the source, framing, language, and editorial choices.

IMPORTANT: Consider the political context of the country the article is about. For example:
- In India: BJP, RSS, Hindutva = right-wing; Congress, AAP, left parties = left-wing
- In the US: Republican, conservative = right-wing; Democrat, liberal = left-wing
- In the UK: Conservative/Tory = right-wing; Labour = left-wing

Classify as exactly one of: left, center-left, center, center-right, right

Respond in this exact JSON format only, no other text:
{"label": "left|center-left|center|center-right|right", "confidence": 0.0-1.0}

Article:
""" + text

    raw = _groq_request_with_retry(
        messages=[
            {"role": "system", "content": "You are a media bias analyst. You classify political leaning of news articles with global political awareness. Respond ONLY with JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=100,
        timeout=15,
    )
    if not raw:
        return None

    try:
        data = _parse_json_from_groq(raw)
        label = data.get("label", "center").lower().strip()
        confidence = float(data.get("confidence", 0.5))

        # Normalize labels
        valid_labels = {"left", "center-left", "center", "center-right", "right"}
        if label not in valid_labels:
            if "left" in label and "center" in label:
                label = "center-left"
            elif "right" in label and "center" in label:
                label = "center-right"
            elif "left" in label:
                label = "left"
            elif "right" in label:
                label = "right"
            else:
                label = "center"

        return {"label": label, "confidence": round(min(max(confidence, 0.0), 1.0), 4)}

    except Exception as e:
        logger.warning(f"Groq political leaning parse failed: {e}")
        return None


def classify_additional_bias(text: str) -> list[dict]:
    """Use Groq to detect granular bias types beyond what the HF classifier catches.
    Covers: gender, religious, caste, ethnic, nationalistic, ageism, disability,
    class/elitism, propaganda, framing, selection, sensationalism, loaded language,
    omission, partisan, corporate, false equivalence, appeal to emotion, cultural."""

    words = text.split()
    if len(words) > 2000:
        text = " ".join(words[:2000])

    prompt = """Analyze this news article for ALL of the following bias types. For each type, provide a confidence score (0.0-1.0). Only include biases you actually detect (score > 0.15).

DEMOGRAPHIC / IDENTITY BIASES:
1. gender_bias - Stereotyping, marginalizing, or favoring based on gender
2. religious_bias - Favoring or demonizing a religion or religious group
3. caste_bias - Bias related to caste hierarchy (especially in South Asian context)
4. ethnic_bias - Bias against or in favor of specific ethnic groups
5. nationalistic_bias - Excessive patriotism, xenophobia, or country-superiority framing
6. ageism - Bias based on age (against young or old)
7. disability_bias - Bias against people with disabilities
8. class_bias - Elitism or bias based on socioeconomic class
9. cultural_bias - Assuming one culture is superior or normative

MEDIA / JOURNALISTIC BIASES:
10. propaganda - Deliberate one-sided messaging to promote a cause
11. framing_bias - Presenting facts in a way that influences interpretation
12. selection_bias - Cherry-picking facts/quotes to support a narrative
13. sensationalism - Exaggerated or dramatic language for emotional response
14. loaded_language - Words with strong connotations beyond literal meaning
15. omission_bias - Leaving out key facts that change conclusions
16. partisan_language - Language clearly favoring one political side
17. corporate_bias - Favoring corporate/business interests
18. false_equivalence - Treating unequal positions as equally valid
19. appeal_to_emotion - Emotional language instead of factual arguments
20. confirmation_bias - Only presenting evidence that confirms a pre-existing view

Respond ONLY with a JSON array of detected biases (score > 0.15):
[{"bias_type": "name", "confidence": 0.0-1.0}]

If none detected, return: []

Article:
""" + text

    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a media bias detection expert. Analyze text for specific bias patterns across demographic, identity, and journalistic dimensions. Respond ONLY with a JSON array."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 800,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            logger.warning("Groq additional bias returned empty choices")
            return []
        raw = choices[0].get("message", {}).get("content", "").strip()
        if not raw:
            return []

        # Parse JSON
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        if not isinstance(data, list):
            return []

        results = []
        for item in data:
            if isinstance(item, dict) and "bias_type" in item and "confidence" in item:
                conf = float(item["confidence"])
                if conf > 0.15:
                    # Normalize underscores to spaces for display
                    btype = item["bias_type"].replace("_", " ")
                    results.append({
                        "bias_type": btype,
                        "confidence": round(conf, 4),
                    })

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    except Exception as e:
        logger.warning(f"Groq additional bias detection failed: {e}")
        return []


def _groq_request_with_retry(messages: list[dict], temperature: float = 0.1, max_tokens: int = 800, timeout: int = 20) -> Optional[str]:
    """Make a Groq API request with retry-on-429 and exponential backoff.

    Returns the response content string, or None if all retries fail.
    """
    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=timeout,
            )
            if resp.status_code == 429:
                retry_after = resp.headers.get("retry-after")
                delay = float(retry_after) if retry_after else _BASE_DELAY * (2 ** attempt)
                logger.warning(
                    f"Groq rate limited (429), attempt {attempt + 1}/{_MAX_RETRIES}, "
                    f"waiting {delay:.1f}s..."
                )
                time.sleep(delay)
                last_error = Exception("Groq rate limited (429)")
                continue

            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                logger.warning("Groq returned empty choices")
                return None
            return choices[0].get("message", {}).get("content", "").strip() or None
        except requests.exceptions.Timeout:
            delay = _BASE_DELAY * (2 ** attempt)
            logger.warning(f"Groq timeout, attempt {attempt + 1}/{_MAX_RETRIES}, retrying in {delay:.1f}s...")
            time.sleep(delay)
            last_error = Exception("Groq timeout")
            continue
        except Exception as e:
            logger.warning(f"Groq request failed: {e}")
            last_error = e
            break

    logger.error(f"Groq request failed after {_MAX_RETRIES} attempts: {last_error}")
    return None


def _parse_json_from_groq(raw: str):
    """Parse JSON from a Groq response, handling ```json fences."""
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


def classify_bias_combined(text: str) -> tuple[dict, list[dict]]:
    """Classify BOTH political leaning AND additional bias types in ONE Groq call.

    Returns (political_leaning_dict, additional_bias_list).
    Falls back to individual calls if the combined call fails.
    """
    words = text.split()
    if len(words) > 2000:
        text = " ".join(words[:2000])

    prompt = """Analyze this news article for:

A) POLITICAL LEANING — Classify as exactly one of: left, center-left, center, center-right, right.
Consider the political context of the country the article is about (e.g. India: BJP/RSS = right, Congress/AAP = left; US: Republican = right, Democrat = left).

B) BIAS TYPES — Detect ALL applicable biases with confidence scores (0.0-1.0). Only include biases with score > 0.15.
Bias types to check: gender_bias, religious_bias, caste_bias, ethnic_bias, nationalistic_bias, ageism, disability_bias, class_bias, cultural_bias, propaganda, framing_bias, selection_bias, sensationalism, loaded_language, omission_bias, partisan_language, corporate_bias, false_equivalence, appeal_to_emotion, confirmation_bias.

Respond ONLY with this exact JSON format, no other text:
{
  "political_leaning": {"label": "left|center-left|center|center-right|right", "confidence": 0.0-1.0},
  "bias_types": [{"bias_type": "name", "confidence": 0.0-1.0}]
}

Article:
""" + text

    raw = _groq_request_with_retry(
        messages=[
            {"role": "system", "content": "You are a media bias analyst. Analyze text for political leaning and specific bias patterns. Respond ONLY with JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=900,
        timeout=25,
    )

    if raw:
        try:
            data = _parse_json_from_groq(raw)

            # Parse political leaning
            pl = data.get("political_leaning", {})
            label = pl.get("label", "center").lower().strip()
            confidence = float(pl.get("confidence", 0.5))
            valid_labels = {"left", "center-left", "center", "center-right", "right"}
            if label not in valid_labels:
                if "left" in label and "center" in label:
                    label = "center-left"
                elif "right" in label and "center" in label:
                    label = "center-right"
                elif "left" in label:
                    label = "left"
                elif "right" in label:
                    label = "right"
                else:
                    label = "center"
            political_leaning = {"label": label, "confidence": round(min(max(confidence, 0.0), 1.0), 4)}

            # Parse bias types
            bias_list = data.get("bias_types", [])
            additional_bias = []
            if isinstance(bias_list, list):
                for item in bias_list:
                    if isinstance(item, dict) and "bias_type" in item and "confidence" in item:
                        conf = float(item["confidence"])
                        if conf > 0.15:
                            btype = item["bias_type"].replace("_", " ")
                            additional_bias.append({"bias_type": btype, "confidence": round(conf, 4)})
                additional_bias.sort(key=lambda x: x["confidence"], reverse=True)

            logger.info(f"Combined bias analysis: leaning={political_leaning['label']}, {len(additional_bias)} bias types")
            return political_leaning, additional_bias

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse combined bias response, falling back: {e}")

    # Fallback: try individual calls
    logger.info("Combined call failed, trying individual Groq calls...")
    political_leaning = classify_political_leaning(text)
    additional_bias = classify_additional_bias(text)
    return political_leaning, additional_bias


def extract_bias_evidence(text: str, top_n: int = 4) -> list[dict]:
    """Find the most biased sentences in the article."""
    classifier = _get_bias_classifier()
    sentences = nltk.sent_tokenize(text)

    scored_sentences = []
    for sent in sentences:
        if len(sent.split()) < 5:
            continue
        try:
            results = classifier(sent)
            if results and isinstance(results[0], list):
                results = results[0]

            # Find highest non-"No Bias" score
            for r in results:
                if r["label"].lower() not in ("no bias", "unbiased", "none"):
                    scored_sentences.append({
                        "sentence": sent.strip(),
                        "bias_type": r["label"],
                        "confidence": round(r["score"], 4),
                    })
                    break
        except Exception:
            continue

    # Sort by confidence and return top N
    scored_sentences.sort(key=lambda x: x["confidence"], reverse=True)
    return scored_sentences[:top_n]


def compute_bias_index(
    bias_types: list[dict],
    political_leaning: dict,
    sentiment_gap: float,
    entity_bias_count: int,
    total_sentences: int,
    biased_sentence_count: int,
) -> tuple[float, dict]:
    """Compute overall bias index (0-100) with breakdown."""

    # 1. Bias type classifier average confidence (weight 0.4)
    if bias_types:
        non_neutral = [b for b in bias_types if b["bias_type"].lower() not in ("no bias", "unbiased", "none")]
        bias_type_score = (sum(b["confidence"] for b in non_neutral[:3]) / max(len(non_neutral[:3]), 1)) * 100 if non_neutral else 0
    else:
        bias_type_score = 0

    # 2. Political leaning extremity (weight 0.2)
    leaning = political_leaning.get("label", "center").lower()
    leaning_conf = political_leaning.get("confidence", 0)
    if leaning == "center":
        leaning_score = (1 - leaning_conf) * 25
    elif leaning in ("center-left", "center-right"):
        leaning_score = leaning_conf * 60
    else:  # left or right
        leaning_score = leaning_conf * 100

    # 3. Headline-body sentiment gap (weight 0.15)
    sentiment_gap_score = min(abs(sentiment_gap) * 100, 100)

    # 4. Entity framing imbalance (weight 0.15)
    entity_score = min(entity_bias_count * 20, 100)

    # 5. Sentence-level bias density (weight 0.1)
    if total_sentences > 0:
        density_score = (biased_sentence_count / total_sentences) * 100
    else:
        density_score = 0

    # Weighted combination
    bias_index = (
        bias_type_score * 0.4
        + leaning_score * 0.2
        + sentiment_gap_score * 0.15
        + entity_score * 0.15
        + density_score * 0.1
    )

    breakdown = {
        "bias_type_signal": round(bias_type_score, 2),
        "political_extremity": round(leaning_score, 2),
        "sentiment_gap": round(sentiment_gap_score, 2),
        "entity_framing": round(entity_score, 2),
        "bias_density": round(density_score, 2),
    }

    return round(min(bias_index, 100), 2), breakdown


def _chunk_text(text: str, max_words: int = 400) -> list[str]:
    """Split text into chunks of approximately max_words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i : i + max_words])
        if chunk.strip():
            chunks.append(chunk)
    return chunks if chunks else [text]


def unload_bias_models():
    """Unload bias models to free GPU memory."""
    global _bias_classifier, _political_classifier
    _bias_classifier = None
    _political_classifier = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Bias models unloaded.")
