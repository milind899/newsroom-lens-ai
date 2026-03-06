export interface BiasEvidence {
  sentence: string;
  bias_type: string;
  confidence: number;
}

export interface BiasTypeResult {
  bias_type: string;
  confidence: number;
}

export interface PoliticalLeaning {
  label: string;
  confidence: number;
}

export interface EntityBias {
  entity: string;
  entity_type: string;
  sentiment: string;
  co_occurring_bias: string[];
}

export interface SentimentResult {
  label: string;
  score: number;
}

export interface SentimentComparison {
  headline: SentimentResult;
  body: SentimentResult;
  sensationalism_flag: boolean;
  sentiment_gap: number;
}

export interface BiasBreakdown {
  bias_type_signal: number;
  political_extremity: number;
  sentiment_gap: number;
  entity_framing: number;
  bias_density: number;
}

export interface BiasResult {
  bias_index: number;
  bias_types: BiasTypeResult[];
  political_leaning: PoliticalLeaning;
  evidence: BiasEvidence[];
  entity_bias_map: EntityBias[];
  bias_breakdown: BiasBreakdown;
}

export interface LanguageInfo {
  detected_language: string;
  language_code: string;
  confidence: number;
  was_translated: boolean;
  is_indian?: boolean;
  translation_method?: string; // "indictrans2" | "groq" | "none"
}

export interface NeutralRewrite {
  original: string;
  neutral: string;
  bias_type: string;
}

export interface SourceCredibility {
  known: boolean;
  domain: string | null;
  reliability_score: number | null;
  bias_rating: string;
  factual_reporting: string;
  category: string;
  description: string;
}

export interface ClaimVerification {
  claim: string;
  verdict: "verified" | "unverified" | "misleading" | "opinion";
  explanation: string;
}

export interface AnalysisResponse {
  title: string;
  source_url: string | null;
  original_text: string;
  translated_text: string | null;
  language: LanguageInfo;
  summary: string[];
  sentiment: SentimentComparison;
  bias: BiasResult;
  neutral_rewrites: NeutralRewrite[];
  source_credibility: SourceCredibility | null;
  claims: ClaimVerification[] | null;
}

export interface CompareResponse {
  source_a: AnalysisResponse;
  source_b: AnalysisResponse;
  bias_index_delta: number;
  bias_type_overlap: string[];
  bias_type_divergence: Record<string, string>;
  sentiment_delta: number;
  entity_framing_comparison: {
    entity: string;
    source_a_sentiment: string;
    source_b_sentiment: string;
    source_a_bias: string[];
    source_b_bias: string[];
  }[];
}
