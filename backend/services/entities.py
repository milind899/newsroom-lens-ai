# Lazy import GLiNER to prevent startup hang
import nltk
import logging

logger = logging.getLogger(__name__)

# punkt_tab already extracted locally

_gliner_model = None


def _get_gliner_model():
    global _gliner_model
    if _gliner_model is None:
        logger.info("Loading GLiNER model...")
        from gliner import GLiNER
        import inspect
        sig = inspect.signature(GLiNER._from_pretrained)
        kwargs = {}
        if "proxies" in sig.parameters:
            kwargs["proxies"] = None
        if "resume_download" in sig.parameters:
            kwargs["resume_download"] = False
        _gliner_model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1", **kwargs)
        logger.info("GLiNER model loaded.")
    return _gliner_model


def extract_entity_bias_map(text: str, bias_evidence: list[dict]) -> list[dict]:
    """Extract entities and map them to bias contexts."""
    try:
        model = _get_gliner_model()
    except Exception as e:
        logger.error(f"GLiNER model load failed, skipping entities: {e}")
        return []

    entity_labels = ["person", "organization", "country", "political party", "politician"]

    # Extract entities from the full text
    try:
        entities = model.predict_entities(text[:3000], entity_labels, threshold=0.4)
    except Exception as e:
        logger.error(f"GLiNER entity extraction failed: {e}")
        return []

    if not entities:
        return []

    # Build entity-bias associations
    sentences = nltk.sent_tokenize(text)
    bias_sentences = {e["sentence"] for e in bias_evidence}

    entity_bias_map = []
    seen_entities = set()

    for ent in entities:
        entity_name = ent["text"].strip()
        entity_type = ent["label"]

        if entity_name.lower() in seen_entities or len(entity_name) < 2:
            continue
        seen_entities.add(entity_name.lower())

        # Find sentences containing this entity
        co_occurring_bias = []
        sentiment = "neutral"

        for sent in sentences:
            if entity_name.lower() in sent.lower():
                # Check if this sentence is among biased sentences
                for ev in bias_evidence:
                    if ev["sentence"] == sent or entity_name.lower() in ev["sentence"].lower():
                        co_occurring_bias.append(ev["bias_type"])
                        if ev["confidence"] > 0.5:
                            sentiment = "negative" if "negative" in ev.get("bias_type", "").lower() else "associated_with_bias"

        entity_bias_map.append({
            "entity": entity_name,
            "entity_type": entity_type,
            "sentiment": sentiment if co_occurring_bias else "neutral",
            "co_occurring_bias": list(set(co_occurring_bias)),
        })

    # Sort by number of bias associations
    entity_bias_map.sort(key=lambda x: len(x["co_occurring_bias"]), reverse=True)
    return entity_bias_map[:10]


def unload_gliner_model():
    """Unload GLiNER model to free memory."""
    global _gliner_model
    _gliner_model = None
    logger.info("GLiNER model unloaded.")
