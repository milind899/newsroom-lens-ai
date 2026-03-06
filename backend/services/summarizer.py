import requests
import logging
import time
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

# Maximum retries for rate-limited (429) responses
_MAX_RETRIES = 5
_BASE_DELAY = 2  # seconds — doubles each retry

SUMMARY_SYSTEM = "You are a professional news analyst. You summarize articles into 3-5 concise bullet points focusing on key facts only. No opinions, no editorial commentary. Each bullet is one clear sentence starting with a dash (-)."

NEUTRAL_REWRITE_SYSTEM = "You rewrite biased sentences to be factually neutral. Remove emotional, loaded, or biased language while keeping the same factual meaning. Return ONLY the rewritten sentence."

NEUTRAL_BATCH_SYSTEM = (
    "You rewrite biased sentences to be factually neutral. Remove emotional, "
    "loaded, or biased language while keeping the same factual meaning. "
    "You will receive multiple sentences separated by |||SPLIT|||. "
    "Return the neutral rewrites in the SAME order, separated by |||SPLIT|||. "
    "Return ONLY the rewritten sentences, nothing else."
)


def _groq_chat(system: str, user: str, temperature: float = 0.3, max_tokens: int = 500) -> str:
    """Call Groq API with retry-on-429 and exponential backoff."""
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
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=30,
            )

            # Handle rate limiting with retry
            if resp.status_code == 429:
                retry_after = resp.headers.get("retry-after")
                if retry_after:
                    delay = float(retry_after)
                else:
                    delay = _BASE_DELAY * (2 ** attempt)
                logger.warning(
                    f"Groq rate limited (429), attempt {attempt + 1}/{_MAX_RETRIES}, "
                    f"waiting {delay:.1f}s..."
                )
                time.sleep(delay)
                last_error = RuntimeError(f"Groq rate limited (429)")
                continue

            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError(f"Groq returned empty choices: {data}")
            return choices[0].get("message", {}).get("content", "").strip()

        except requests.exceptions.Timeout:
            last_error = RuntimeError("Groq API timed out — try again")
            if attempt < _MAX_RETRIES - 1:
                delay = _BASE_DELAY * (2 ** attempt)
                logger.warning(f"Groq timeout, retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            raise last_error
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Groq API HTTP error: {e.response.status_code} — {e.response.text[:200]}")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Groq API failed: {e}")

    # All retries exhausted
    raise last_error or RuntimeError("Groq API failed after all retries")


def summarize_article(text: str) -> list[str]:
    """Summarize article using Groq API."""
    words = text.split()
    if len(words) > 3000:
        text = " ".join(words[:3000])

    try:
        raw = _groq_chat(
            SUMMARY_SYSTEM,
            f"Summarize this article in 3-5 bullet points:\n\n{text}",
            temperature=0.3,
            max_tokens=500,
        )

        bullets = []
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*") or line.startswith("•"):
                cleaned = line.lstrip("-*• ").strip()
                if cleaned:
                    bullets.append(cleaned)

        if not bullets:
            sentences = raw.split(". ")
            bullets = [s.strip() + "." for s in sentences if len(s.strip()) > 20][:5]

        return bullets[:5] if bullets else ["Summary could not be generated."]
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return [f"Summarization error: {str(e)}"]


def neutral_rewrite(sentence: str) -> str:
    """Rewrite a biased sentence in neutral language using Groq."""
    try:
        return _groq_chat(
            NEUTRAL_REWRITE_SYSTEM,
            f"Rewrite this sentence neutrally:\n\n{sentence}",
            temperature=0.2,
            max_tokens=200,
        )
    except Exception as e:
        logger.error(f"Neutral rewrite failed: {e}")
        return sentence


def neutral_rewrite_batch(sentences: list[str]) -> list[str]:
    """Rewrite multiple biased sentences in ONE Groq call to save rate-limit budget.

    Falls back to returning the originals if the call fails.
    """
    if not sentences:
        return []
    if len(sentences) == 1:
        return [neutral_rewrite(sentences[0])]

    combined = " |||SPLIT||| ".join(sentences)
    try:
        raw = _groq_chat(
            NEUTRAL_BATCH_SYSTEM,
            f"Rewrite these sentences neutrally:\n\n{combined}",
            temperature=0.2,
            max_tokens=300 * len(sentences),
        )
        parts = [p.strip() for p in raw.split("|||SPLIT|||")]
        # If the model returned the correct number of parts, use them
        if len(parts) == len(sentences):
            return parts
        # If it returned more/fewer, pad or truncate
        logger.warning(
            f"Batch rewrite returned {len(parts)} parts for {len(sentences)} inputs, "
            "falling back to individual calls"
        )
        return [neutral_rewrite(s) for s in sentences]
    except Exception as e:
        logger.error(f"Batch neutral rewrite failed: {e}")
        return list(sentences)  # return originals
