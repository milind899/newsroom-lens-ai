from fastapi import APIRouter, HTTPException
from models.schemas import CompareRequest, CompareResponse
from services.extractor import extract_from_url
from services.language import detect_language
from services.translator import translate_to_english, unload_translation_model, get_translation_method, is_indian_language, translate_output_batch
from services.summarizer import summarize_article, neutral_rewrite_batch
from services.sentiment import compare_headline_body_sentiment, unload_sentiment_model
from services.bias import classify_bias_types, classify_bias_combined, extract_bias_evidence, compute_bias_index, unload_bias_models
from services.entities import extract_entity_bias_map, unload_gliner_model
from models.schemas import AnalysisResponse
import nltk
import torch
import logging
import asyncio

# punkt_tab already extracted locally

logger = logging.getLogger(__name__)
router = APIRouter()


def _run_single_analysis(url: str, output_language: str = "en") -> AnalysisResponse:
    """Run full analysis pipeline on a single URL."""
    logger.info(f"[Compare] Starting extraction for {url}")
    try:
        article = extract_from_url(url)
    except Exception as e:
        logger.error(f"[Compare] Extraction failed for {url}: {e}")
        raise ValueError(f"Could not extract article from {url}: {e}")

    if not article["text"] or len(article["text"].strip()) < 30:
        raise ValueError(f"Extracted text too short from {url}")

    original_text = article["text"]
    title = article.get("title", "Untitled")

    logger.info(f"[Compare] Extracted: '{title}' ({len(original_text)} chars)")

    lang_info = detect_language(original_text)
    logger.info(f"[Compare] Language: {lang_info['detected_language']}")

    translated_text = None
    analysis_text = original_text
    if not lang_info["is_english"]:
        translated_text = translate_to_english(original_text, lang_info["language_code"])
        analysis_text = translated_text
        unload_translation_model()
        logger.info(f"[Compare] Translation done")

    # HuggingFace model inference (GPU)
    logger.info(f"[Compare] Running sentiment...")
    sentiment_result = compare_headline_body_sentiment(title, analysis_text)
    logger.info(f"[Compare] Running bias classification...")
    bias_types = classify_bias_types(analysis_text)
    bias_evidence = extract_bias_evidence(analysis_text)
    logger.info(f"[Compare] Running entity extraction...")
    entity_bias_map = extract_entity_bias_map(analysis_text, bias_evidence)

    # Unload all HuggingFace/CUDA models before Groq API calls (VRAM sequencing)
    logger.info(f"[Compare] Unloading GPU models...")
    unload_sentiment_model()
    unload_bias_models()
    unload_gliner_model()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Groq API calls — combined call saves rate-limit budget (1 call instead of 2)
    logger.info(f"[Compare] Groq: combined political leaning + additional bias...")
    political_leaning, additional_bias = classify_bias_combined(analysis_text)
    existing_types = {b["bias_type"].lower() for b in bias_types}
    for ab in additional_bias:
        if ab["bias_type"].lower() not in existing_types:
            bias_types.append(ab)
            existing_types.add(ab["bias_type"].lower())
    bias_types.sort(key=lambda x: x["confidence"], reverse=True)

    sentences = nltk.sent_tokenize(analysis_text)
    bias_index, bias_breakdown = compute_bias_index(
        bias_types=bias_types,
        political_leaning=political_leaning,
        sentiment_gap=sentiment_result["sentiment_gap"],
        entity_bias_count=len([e for e in entity_bias_map if e["co_occurring_bias"]]),
        total_sentences=len(sentences),
        biased_sentence_count=len(bias_evidence),
    )

    logger.info(f"[Compare] Groq: summarizing...")
    summary = summarize_article(analysis_text)

    # Batch neutral rewrites — 1 Groq call instead of 3
    logger.info(f"[Compare] Groq: batch neutral rewrites...")
    evidence_sentences = [ev["sentence"] for ev in bias_evidence[:3]]
    rewritten_sentences = neutral_rewrite_batch(evidence_sentences)
    neutral_rewrites = []
    for i, ev in enumerate(bias_evidence[:3]):
        neutral_rewrites.append({
            "original": ev["sentence"],
            "neutral": rewritten_sentences[i] if i < len(rewritten_sentences) else ev["sentence"],
            "bias_type": ev["bias_type"],
        })

    # Translate output if a non-English language was requested
    if output_language and output_language != "en":
        logger.info(f"[Compare] Translating output to {output_language}...")
        all_texts = list(summary) + [rw["neutral"] for rw in neutral_rewrites]
        translated_all = translate_output_batch(all_texts, output_language)
        n_summary = len(summary)
        summary = translated_all[:n_summary]
        rewrite_translations = translated_all[n_summary:]
        for i, rw in enumerate(neutral_rewrites):
            if i < len(rewrite_translations):
                rw["neutral"] = rewrite_translations[i]
        logger.info(f"[Compare] Output translation complete.")

    logger.info(f"[Compare] Pipeline complete for {url}")

    return AnalysisResponse(
        title=title,
        source_url=url,
        original_text=original_text[:5000],
        translated_text=translated_text[:5000] if translated_text else None,
        language={
            "detected_language": lang_info["detected_language"],
            "language_code": lang_info["language_code"],
            "confidence": lang_info["confidence"],
            "was_translated": not lang_info["is_english"],
            "is_indian": is_indian_language(lang_info["language_code"]),
            "translation_method": get_translation_method(lang_info["language_code"]),
        },
        summary=summary,
        sentiment={
            "headline": sentiment_result["headline"],
            "body": sentiment_result["body"],
            "sensationalism_flag": sentiment_result["sensationalism_flag"],
            "sentiment_gap": sentiment_result["sentiment_gap"],
        },
        bias={
            "bias_index": bias_index,
            "bias_types": bias_types[:12],
            "political_leaning": political_leaning,
            "evidence": bias_evidence,
            "entity_bias_map": entity_bias_map,
            "bias_breakdown": bias_breakdown,
        },
        neutral_rewrites=neutral_rewrites,
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_sources(request: CompareRequest):
    """Compare bias between two news sources on the same topic."""
    loop = asyncio.get_running_loop()
    output_language = getattr(request, "output_language", "en") or "en"

    try:
        logger.info(f"Comparing source A: {request.url_a}")
        source_a = await loop.run_in_executor(None, _run_single_analysis, request.url_a, output_language)
    except Exception as e:
        logger.error(f"Source A analysis failed: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to analyze source A: {str(e)}")

    try:
        logger.info(f"Comparing source B: {request.url_b}")
        source_b = await loop.run_in_executor(None, _run_single_analysis, request.url_b, output_language)
    except Exception as e:
        logger.error(f"Source B analysis failed: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to analyze source B: {str(e)}")

    # Compute deltas
    bias_index_delta = abs(source_a.bias.bias_index - source_b.bias.bias_index)

    types_a = {bt.bias_type for bt in source_a.bias.bias_types[:12]}
    types_b = {bt.bias_type for bt in source_b.bias.bias_types[:12]}
    bias_type_overlap = list(types_a & types_b)

    bias_type_divergence = {}
    for t in types_a - types_b:
        bias_type_divergence[t] = "only in Source A"
    for t in types_b - types_a:
        bias_type_divergence[t] = "only in Source B"

    sentiment_delta = abs(source_a.sentiment.sentiment_gap - source_b.sentiment.sentiment_gap)

    # Entity framing comparison
    entities_a = {e.entity.lower(): e for e in source_a.bias.entity_bias_map}
    entities_b = {e.entity.lower(): e for e in source_b.bias.entity_bias_map}
    shared_entities = set(entities_a.keys()) & set(entities_b.keys())

    entity_framing_comparison = []
    for ent_name in shared_entities:
        ea = entities_a[ent_name]
        eb = entities_b[ent_name]
        entity_framing_comparison.append({
            "entity": ent_name,
            "source_a_sentiment": ea.sentiment,
            "source_b_sentiment": eb.sentiment,
            "source_a_bias": ea.co_occurring_bias,
            "source_b_bias": eb.co_occurring_bias,
        })

    return CompareResponse(
        source_a=source_a,
        source_b=source_b,
        bias_index_delta=round(bias_index_delta, 2),
        bias_type_overlap=bias_type_overlap,
        bias_type_divergence=bias_type_divergence,
        sentiment_delta=round(sentiment_delta, 4),
        entity_framing_comparison=entity_framing_comparison,
    )
