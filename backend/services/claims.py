"""
Claim extraction and verification service.

Uses Groq LLM to extract key factual claims from a news article and
classify each as verified / unverified / misleading / opinion.
"""

import json
import logging
import requests
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Groq API config (same key as other services)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"


def extract_and_verify_claims(text: str) -> list[dict]:
    """Extract 3-5 key factual claims from article text and classify each.

    Each claim is classified as one of:
      - "verified"   : widely reported, established fact
      - "unverified" : claim made without supporting evidence
      - "misleading" : partially true but framed in a misleading way
      - "opinion"    : stated as fact but is actually an opinion

    Returns a list of dicts: [{"claim": str, "verdict": str, "explanation": str}, ...]
    Returns an empty list on any failure.
    """
    # Truncate to 2000 words to stay within context limits
    words = text.split()
    if len(words) > 2000:
        text = " ".join(words[:2000])

    prompt = (
        "Analyze the following news article. Extract 3 to 5 key factual claims "
        "made in the article.\n\n"
        "For each claim, classify it as exactly one of:\n"
        '- "verified" — a widely reported and established fact\n'
        '- "unverified" — a claim made without clear supporting evidence\n'
        '- "misleading" — partially true but framed in a misleading way\n'
        '- "opinion" — presented as fact but is actually an opinion or subjective judgment\n\n'
        "Respond ONLY with a JSON array in this exact format, no other text:\n"
        '[{"claim": "...", "verdict": "verified|unverified|misleading|opinion", '
        '"explanation": "one sentence explaining why"}]\n\n'
        "Article:\n" + text
    )

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
                    {
                        "role": "system",
                        "content": (
                            "You are a fact-checking analyst. You extract key factual "
                            "claims from news articles and assess their veracity. "
                            "Respond ONLY with a JSON array."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 1024,
            },
            timeout=20,
        )
        resp.raise_for_status()

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            logger.warning("Groq claims extraction returned empty choices")
            return []

        raw = choices[0].get("message", {}).get("content", "").strip()
        if not raw:
            logger.warning("Groq claims extraction returned empty content")
            return []

        # Strip ```json ... ``` wrapper if the LLM added one
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            logger.warning("Groq claims response is not a list: %s", type(parsed))
            return []

        # Validate and normalize each entry
        valid_verdicts = {"verified", "unverified", "misleading", "opinion"}
        results = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            claim = item.get("claim", "").strip()
            verdict = item.get("verdict", "").strip().lower()
            explanation = item.get("explanation", "").strip()
            if not claim or not verdict:
                continue
            if verdict not in valid_verdicts:
                verdict = "unverified"
            results.append({
                "claim": claim,
                "verdict": verdict,
                "explanation": explanation,
            })

        return results

    except Exception as e:
        logger.warning("Groq claim extraction failed: %s", e)
        return []
