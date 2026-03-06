from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import nltk
import torch
import logging
import asyncio

from models.schemas import AnalysisRequest, AnalysisResponse
from services.extractor import extract_from_url, extract_from_text
from services.pdf_extractor import extract_from_pdf
from services.language import detect_language
from services.translator import translate_to_english, unload_translation_model, get_translation_method, is_indian_language, translate_output, translate_output_batch
from services.summarizer import summarize_article, neutral_rewrite
from services.sentiment import compare_headline_body_sentiment, unload_sentiment_model
from services.bias import classify_bias_types, classify_political_leaning, extract_bias_evidence, compute_bias_index, unload_bias_models, classify_additional_bias
from services.entities import extract_entity_bias_map, unload_gliner_model
from services.credibility import get_source_credibility
from services.claims import extract_and_verify_claims

# punkt_tab already extracted locally

logger = logging.getLogger(__name__)
router = APIRouter()


def _run_analysis_pipeline(url, text_input, file_bytes, file_name, output_language):
    """Synchronous analysis pipeline — runs in thread pool to avoid blocking event loop."""

    # Step 1: Extract article
    if url:
        logger.info(f"Extracting article from URL: {url}")
        article = extract_from_url(url)
    elif file_bytes:
        logger.info(f"Extracting from PDF: {file_name}")
        article = extract_from_pdf(file_bytes, file_name)
    elif text_input:
        logger.info("Processing direct text input")
        article = extract_from_text(text_input)
    else:
        raise ValueError("No input provided")

    if not article["text"] or len(article["text"].strip()) < 30:
        raise ValueError("Extracted text is too short for analysis. Try pasting the article text directly in the Text tab.")

    original_text = article["text"]
    title = article.get("title", "Untitled")

    # Step 2: Detect language
    lang_info = detect_language(original_text)
    logger.info(f"Detected language: {lang_info['detected_language']} ({lang_info['confidence']})")

    # Step 3: Translate if needed
    translated_text = None
    analysis_text = original_text
    if not lang_info["is_english"]:
        logger.info(f"Translating from {lang_info['detected_language']} to English...")
        translated_text = translate_to_english(original_text, lang_info["language_code"])
        analysis_text = translated_text
        unload_translation_model()
        logger.info("Translation complete, model unloaded.")

    # Step 4: Sentiment analysis
    logger.info("Running sentiment analysis...")
    sentiment_result = compare_headline_body_sentiment(title, analysis_text)

    # Step 5: Bias analysis (HuggingFace models — runs on GPU)
    logger.info("Running bias classification...")
    bias_types = classify_bias_types(analysis_text)
    bias_evidence = extract_bias_evidence(analysis_text)

    # Step 6: Entity-bias mapping
    logger.info("Extracting entity-bias map...")
    entity_bias_map = extract_entity_bias_map(analysis_text, bias_evidence)

    # Unload all HuggingFace/CUDA models before running Groq API (VRAM sequencing)
    logger.info("Unloading transformers models to free VRAM for Groq...")
    unload_sentiment_model()
    unload_bias_models()
    unload_gliner_model()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("VRAM freed. Starting Groq inference.")

    # Step 7: Political leaning via Groq (globally aware, not US-centric)
    logger.info("Classifying political leaning via Groq...")
    political_leaning = classify_political_leaning(analysis_text)

    # Step 7b: Additional bias types via Groq (propaganda, framing, loaded language, etc.)
    logger.info("Detecting additional bias types via Groq...")
    additional_bias = classify_additional_bias(analysis_text)

    # Merge HF bias types with Groq additional types (deduplicate by name)
    existing_types = {b["bias_type"].lower() for b in bias_types}
    for ab in additional_bias:
        if ab["bias_type"].lower() not in existing_types:
            bias_types.append(ab)
            existing_types.add(ab["bias_type"].lower())
    # Re-sort by confidence
    bias_types.sort(key=lambda x: x["confidence"], reverse=True)

    # Step 7c: Compute bias index
    sentences = nltk.sent_tokenize(analysis_text)
    bias_index, bias_breakdown = compute_bias_index(
        bias_types=bias_types,
        political_leaning=political_leaning,
        sentiment_gap=sentiment_result["sentiment_gap"],
        entity_bias_count=len([e for e in entity_bias_map if e["co_occurring_bias"]]),
        total_sentences=len(sentences),
        biased_sentence_count=len(bias_evidence),
    )

    # Step 8: Summarize
    logger.info("Generating summary...")
    summary = summarize_article(analysis_text)

    # Step 8b: Source credibility (instant local lookup, no API)
    source_credibility = None
    if url:
        logger.info("Looking up source credibility...")
        source_credibility = get_source_credibility(url)

    # Step 8c: Claim extraction & verification (ONE Groq call)
    logger.info("Extracting and verifying claims...")
    claims = extract_and_verify_claims(analysis_text)

    # Step 9: Neutral rewrites of biased sentences
    logger.info("Generating neutral rewrites...")
    neutral_rewrites = []
    for ev in bias_evidence[:3]:  # Top 3 most biased sentences
        rewritten = neutral_rewrite(ev["sentence"])
        neutral_rewrites.append({
            "original": ev["sentence"],
            "neutral": rewritten,
            "bias_type": ev["bias_type"],
        })

    # Step 10: Translate output to target language if needed
    #   - Indian languages: IndicTrans2 local model (no API, one GPU batch)
    #   - Other languages:  Groq API fallback
    if output_language and output_language != "en":
        logger.info(f"Translating output to {output_language}...")

        # Collect all texts to translate in one batch
        all_texts = list(summary) + [rw["neutral"] for rw in neutral_rewrites]
        translated_all = translate_output_batch(all_texts, output_language)

        n_summary = len(summary)
        summary = translated_all[:n_summary]
        rewrite_translations = translated_all[n_summary:]
        for i, rw in enumerate(neutral_rewrites):
            if i < len(rewrite_translations):
                rw["neutral"] = rewrite_translations[i]

        logger.info(f"Output translation to {output_language} complete.")

    # Build response
    response = AnalysisResponse(
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
        source_credibility=source_credibility,
        claims=claims,
    )

    logger.info(f"Analysis complete. Bias Index: {bias_index}")
    return response


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_article(
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    output_language: Optional[str] = Form("en"),
):
    """Full analysis pipeline: extract -> detect language -> translate -> summarize -> bias -> sentiment."""

    if not url and not text and not file:
        raise HTTPException(status_code=400, detail="Provide a URL, text, or PDF file.")

    # Read file bytes before entering the thread pool (UploadFile is async)
    file_bytes = None
    file_name = None
    if file:
        file_bytes = await file.read()
        file_name = file.filename

    loop = asyncio.get_running_loop()
    try:
        response = await loop.run_in_executor(
            None,
            _run_analysis_pipeline,
            url, text, file_bytes, file_name, output_language,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
