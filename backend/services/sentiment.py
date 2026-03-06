from transformers import pipeline
import torch
import logging

logger = logging.getLogger(__name__)

_sentiment_pipeline = None


def _get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        logger.info("Loading sentiment analysis model...")
        device = 0 if torch.cuda.is_available() else -1
        _sentiment_pipeline = pipeline(
            "text-classification",
            model="tabularisai/multilingual-sentiment-analysis",
            top_k=None,
            device=device,
            truncation=True,
            max_length=512,
            model_kwargs={"low_cpu_mem_usage": True, "torch_dtype": torch.float16},
        )
        logger.info("Sentiment model loaded.")
    return _sentiment_pipeline


def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment of text. Returns {label, score}."""
    pipe = _get_sentiment_pipeline()
    try:
        # Truncate to 512 tokens worth
        words = text.split()
        if len(words) > 400:
            text = " ".join(words[:400])

        results = pipe(text)
        if results and isinstance(results[0], list):
            results = results[0]

        # Find the top result
        best = max(results, key=lambda x: x["score"])
        return {"label": best["label"], "score": round(best["score"], 4)}
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {"label": "neutral", "score": 0.5}


def compare_headline_body_sentiment(headline: str, body: str) -> dict:
    """Compare sentiment between headline and body to detect sensationalism."""
    headline_sent = analyze_sentiment(headline)
    body_sent = analyze_sentiment(body)

    # Map sentiments to numeric scale for gap calculation
    sentiment_values = {
        "very negative": -1.0,
        "negative": -0.5,
        "neutral": 0.0,
        "positive": 0.5,
        "very positive": 1.0,
        # Fallbacks
        "1 star": -1.0,
        "2 stars": -0.5,
        "3 stars": 0.0,
        "4 stars": 0.5,
        "5 stars": 1.0,
    }

    h_val = sentiment_values.get(headline_sent["label"].lower(), 0.0)
    b_val = sentiment_values.get(body_sent["label"].lower(), 0.0)
    gap = abs(h_val - b_val)

    return {
        "headline": headline_sent,
        "body": body_sent,
        "sentiment_gap": round(gap, 4),
        "sensationalism_flag": gap > 0.5,
    }


def unload_sentiment_model():
    """Unload sentiment model to free memory."""
    global _sentiment_pipeline
    _sentiment_pipeline = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Sentiment model unloaded.")
