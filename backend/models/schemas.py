from pydantic import BaseModel
from typing import Optional


class AnalysisRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None


class BiasEvidence(BaseModel):
    sentence: str
    bias_type: str
    confidence: float


class BiasTypeResult(BaseModel):
    bias_type: str
    confidence: float


class PoliticalLeaning(BaseModel):
    label: str  # left / center / right
    confidence: float


class EntityBias(BaseModel):
    entity: str
    entity_type: str
    sentiment: str
    co_occurring_bias: list[str]


class SentimentResult(BaseModel):
    label: str
    score: float


class SentimentComparison(BaseModel):
    headline: SentimentResult
    body: SentimentResult
    sensationalism_flag: bool
    sentiment_gap: float


class BiasResult(BaseModel):
    bias_index: float  # 0-100
    bias_types: list[BiasTypeResult]
    political_leaning: PoliticalLeaning
    evidence: list[BiasEvidence]
    entity_bias_map: list[EntityBias]
    bias_breakdown: dict[str, float]


class LanguageInfo(BaseModel):
    detected_language: str
    language_code: str
    confidence: float
    was_translated: bool
    is_indian: bool = False
    translation_method: str = "none"


class AnalysisResponse(BaseModel):
    title: str
    source_url: Optional[str] = None
    original_text: str
    translated_text: Optional[str] = None
    language: LanguageInfo
    summary: list[str]
    sentiment: SentimentComparison
    bias: BiasResult
    neutral_rewrites: list[dict[str, str]]
    source_credibility: Optional[dict] = None
    claims: Optional[list[dict]] = None


class CompareRequest(BaseModel):
    url_a: str
    url_b: str
    output_language: Optional[str] = "en"


class CompareResponse(BaseModel):
    source_a: AnalysisResponse
    source_b: AnalysisResponse
    bias_index_delta: float
    bias_type_overlap: list[str]
    bias_type_divergence: dict[str, str]
    sentiment_delta: float
    entity_framing_comparison: list[dict]
