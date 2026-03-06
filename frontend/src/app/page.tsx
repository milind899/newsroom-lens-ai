"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import InputPanel from "@/components/InputPanel";
import BiasPanel from "@/components/BiasPanel";
import EvidencePanel from "@/components/EvidencePanel";
import EntityGraph from "@/components/EntityGraph";
import SummaryPanel from "@/components/SummaryPanel";
import SentimentPanel from "@/components/SentimentPanel";
import NeutralRewritePanel from "@/components/NeutralRewritePanel";
import CompareView from "@/components/CompareView";
import CredibilityPanel from "@/components/CredibilityPanel";
import ClaimsPanel from "@/components/ClaimsPanel";
import { analyzeArticle, compareSources, downloadPdfReport } from "@/lib/api";
import { AnalysisResponse, CompareResponse } from "@/lib/types";

// ── Pipeline Steps ───────────────────────────────────────────
const PIPELINE = [
  "Extracting article content",
  "Detecting language",
  "Translating (IndicTrans2 / Groq)",
  "Running bias classification",
  "Analyzing sentiment",
  "Mapping entities",
  "Generating summary",
  "Verifying claims",
  "Writing neutral rewrites",
];

// ── Stat Cell ────────────────────────────────────────────────
function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center px-6 py-5 border-r border-[#2e2e2e] last:border-0">
      <div
        className="text-4xl font-display font-bold leading-none mb-1"
        style={{ color: "#d4372c", fontFamily: "Syne, sans-serif" }}
      >
        {value}
      </div>
      <div
        className="text-[10px] uppercase tracking-widest"
        style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
      >
        {label}
      </div>
    </div>
  );
}

// ── Feature Row ──────────────────────────────────────────────
function FeatureRow({
  num,
  title,
  desc,
}: {
  num: string;
  title: string;
  desc: string;
}) {
  return (
    <div className="flex gap-5 py-4 border-b border-[#1e1e1e] last:border-0">
      <span
        className="text-xs mt-0.5 shrink-0 w-5"
        style={{ color: "#d4372c", fontFamily: "DM Mono, monospace" }}
      >
        {num}
      </span>
      <div>
        <div
          className="text-sm font-semibold mb-0.5"
          style={{ color: "#e8e2d8" }}
        >
          {title}
        </div>
        <div className="text-sm" style={{ color: "#5a5450" }}>
          {desc}
        </div>
      </div>
    </div>
  );
}

// ── Loading Stage ────────────────────────────────────────────
function LoadingView({ stage }: { stage: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="max-w-lg mx-auto"
    >
      <div className="panel">
        <div className="panel-header">
          <div
            className="w-3 h-3 rounded-full animate-spin border-2"
            style={{ borderColor: "#2e2e2e", borderTopColor: "#d4372c" }}
          />
          <span className="text-base text-[var(--chalk)]">Processing</span>
          <span
            className="ml-auto text-[10px]"
            style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
          >
            First run downloads models
          </span>
        </div>
        <div className="panel-body space-y-1">
          {PIPELINE.map((step, i) => {
            const done = i < stage;
            const active = i === stage;
            return (
              <div
                key={step}
                className="flex items-center gap-3 py-1.5"
                style={{ opacity: done ? 0.35 : active ? 1 : 0.4 }}
              >
                <div
                  className="w-4 h-4 rounded-sm shrink-0 flex items-center justify-center text-[9px]"
                  style={{
                    background: done
                      ? "#1e7c4a"
                      : active
                      ? "#d4372c"
                      : "#222",
                    color: "white",
                    fontFamily: "DM Mono, monospace",
                  }}
                >
                  {done ? "✓" : i + 1}
                </div>
                <span
                  className="text-sm"
                  style={{
                    color: active ? "#e8e2d8" : "#5a5450",
                    fontFamily: active ? "DM Sans, sans-serif" : undefined,
                  }}
                >
                  {step}
                </span>
                {active && (
                  <div
                    className="ml-auto w-3 h-3 rounded-full animate-pulse-dot"
                    style={{ background: "#d4372c" }}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}

// ── Main Page ────────────────────────────────────────────────
export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [mode, setMode] = useState<"single" | "compare">("single");
  const [stage, setStage] = useState(0);
  const [started, setStarted] = useState(false);

  const inputRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const runAnalysis = async (params: { url?: string; text?: string; file?: File; output_language?: string }) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setCompareResult(null);
    setMode("single");
    setStarted(true);
    setStage(0);
    const iv = setInterval(() => setStage((s) => Math.min(s + 1, PIPELINE.length - 1)), 6000);
    try {
      const data = await analyzeArticle(params);
      clearInterval(iv);
      setResult(data);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth" }), 80);
    } catch (e: unknown) {
      clearInterval(iv);
      let msg = "Analysis failed. Check backend is running.";
      if (e && typeof e === "object" && "response" in e) {
        const axErr = e as { response?: { data?: { detail?: string } } };
        msg = axErr.response?.data?.detail || (e instanceof Error ? e.message : msg);
      } else if (e instanceof Error) {
        msg = e.message;
      }
      setError(msg);
    } finally {
      setLoading(false);
      setStage(0);
    }
  };

  const runCompare = async (urlA: string, urlB: string, outputLang: string) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setCompareResult(null);
    setMode("compare");
    setStarted(true);
    setStage(0);
    const iv = setInterval(() => setStage((s) => Math.min(s + 1, PIPELINE.length - 1)), 15000);
    try {
      const data = await compareSources(urlA, urlB, outputLang);
      clearInterval(iv);
      setCompareResult(data);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth" }), 80);
    } catch (e: unknown) {
      clearInterval(iv);
      let msg = "Comparison failed. Check backend is running.";
      if (e && typeof e === "object" && "response" in e) {
        const axErr = e as { response?: { data?: { detail?: string } } };
        msg = axErr.response?.data?.detail || (e instanceof Error ? e.message : msg);
      } else if (e instanceof Error) {
        msg = e.message;
      }
      setError(msg);
    } finally {
      setLoading(false);
      setStage(0);
    }
  };

  const scrollToInput = () =>
    inputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });

  const showHero = !started && !result && !compareResult;

  return (
    <div className="min-h-screen" style={{ background: "#0d0d0d" }}>
      {/* ── Nav ─────────────────────────────────────────────── */}
      <nav
        className="fixed top-0 left-0 right-0 z-50"
        style={{
          background: "rgba(13,13,13,0.92)",
          backdropFilter: "blur(8px)",
          borderBottom: "1px solid #1e1e1e",
        }}
      >
        <div className="max-w-6xl mx-auto px-6 h-12 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span
              className="text-sm font-display font-bold tracking-tight"
              style={{ color: "#e8e2d8", fontFamily: "Syne, sans-serif" }}
            >
              NEWSROOM LENS
            </span>
            <div className="w-px h-4" style={{ background: "#2e2e2e" }} />
            <span
              className="text-[10px] uppercase tracking-widest hidden sm:block"
              style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
            >
              Bias Intelligence
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2">
              <span className="live-dot animate-pulse-dot" />
              <span
                className="text-[10px] uppercase tracking-widest"
                style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
              >
                Local inference
              </span>
            </div>
            <button
              onClick={scrollToInput}
              className="btn-primary"
              style={{ padding: "7px 16px", fontSize: "10px" }}
            >
              Analyze
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────── */}
      {showHero && (
        <section className="relative pt-12">
          {/* dot grid bg */}
          <div
            className="absolute inset-0 pointer-events-none dot-grid"
            style={{ opacity: 0.4 }}
          />
          {/* red glow */}
          <div
            className="absolute pointer-events-none"
            style={{
              top: "10%",
              left: "50%",
              transform: "translateX(-50%)",
              width: 480,
              height: 280,
              background: "radial-gradient(ellipse, rgba(212,55,44,0.08) 0%, transparent 70%)",
            }}
          />

          <div className="relative max-w-6xl mx-auto px-6">
            {/* Header row */}
            <div
              className="flex items-center gap-3 pt-16 pb-8"
              style={{ borderBottom: "1px solid #1e1e1e" }}
            >
              <span
                className="text-[10px] uppercase tracking-widest"
                style={{ color: "#d4372c", fontFamily: "DM Mono, monospace" }}
              >
                Vol. I — No. 1
              </span>
              <div className="flex-1 h-px" style={{ background: "#1e1e1e" }} />
              <span
                className="text-[10px] uppercase tracking-widest"
                style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
              >
                {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
              </span>
            </div>

            {/* Main hero */}
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55 }}
              className="py-16 max-w-3xl"
            >
              <h1
                className="font-display leading-[1.05] mb-6"
                style={{
                  fontFamily: "Syne, sans-serif",
                  fontSize: "clamp(2.6rem, 6vw, 4.5rem)",
                  fontWeight: 800,
                  color: "#e8e2d8",
                  letterSpacing: "-0.02em",
                }}
              >
                The news machine
                <br />
                has a{" "}
                <span style={{ color: "#d4372c" }}>bias problem.</span>
                <br />
                We measure it.
              </h1>
              <p
                className="text-base max-w-xl mb-8 leading-relaxed"
                style={{ color: "#9a9490" }}
              >
                Paste any article URL and get a full bias audit — political
                leaning, framing signals, sensationalism, entity associations,
                and a neutral rewrite. Runs on your machine, no cloud.
              </p>
              <button onClick={scrollToInput} className="btn-primary">
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
                Start analyzing
              </button>
            </motion.div>

            {/* Stats strip */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="flex justify-start mb-16"
              style={{
                border: "1px solid #2e2e2e",
                borderRadius: 3,
                display: "inline-flex",
              }}
            >
              <Stat value="20" label="Bias types" />
              <Stat value="40+" label="Languages" />
              <Stat value="32" label="Source ratings" />
              <Stat value="0 KB" label="Cloud sent" />
            </motion.div>

            {/* Features list */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="grid md:grid-cols-2 gap-x-12 mb-20"
              style={{ borderTop: "1px solid #1e1e1e", paddingTop: 0 }}
            >
              <div>
                <FeatureRow
                  num="01"
                  title="Bias Index (0–100)"
                  desc="Ensemble score from ModernBERT, political classifier, entity framing, sentiment gap, and bias density."
                />
                <FeatureRow
                  num="02"
                  title="Political Leaning Detector"
                  desc="Classifies left / center / right with confidence score using a fine-tuned BERT model."
                />
                <FeatureRow
                  num="03"
                  title="Evidence Extraction"
                  desc="Surfaces the exact biased sentences with bias-type labels and confidence percentages."
                />
                <FeatureRow
                  num="04"
                  title="Source Credibility Score"
                  desc="MBFC-style reliability rating, factual reporting grade, and bias rating for 32+ known sources."
                />
              </div>
              <div>
                <FeatureRow
                  num="05"
                  title="Claim Verification"
                  desc="Extracts key factual claims and classifies each as verified, unverified, misleading, or opinion."
                />
                <FeatureRow
                  num="06"
                  title="Entity-Bias Mapping"
                  desc="GLiNER NER identifies people and organizations mentioned near flagged language."
                />
                <FeatureRow
                  num="07"
                  title="Sensationalism Detection"
                  desc="Compares headline vs body sentiment; flags when headlines exaggerate tone for clicks."
                />
                <FeatureRow
                  num="08"
                  title="Neutral Rewrites"
                  desc="Mistral 7B re-writes biased sentences in neutral language for direct comparison."
                />
              </div>
            </motion.div>
          </div>
          <div className="rule" />
        </section>
      )}

      {/* ── Input Section ────────────────────────────────────── */}
      <section
        ref={inputRef}
        className={`max-w-6xl mx-auto px-6 ${showHero ? "py-16" : "pt-20 pb-8"}`}
      >
        {!showHero && (
          <div className="mb-6 flex items-center justify-between" style={{ borderBottom: "1px solid #1e1e1e", paddingBottom: 16 }}>
            <span
              className="text-xs uppercase tracking-widest"
              style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
            >
              {result
                ? `Analysis — ${result.title}`
                : compareResult
                ? "Source Comparison"
                : "New analysis"}
            </span>
            {result && (
              <button
                onClick={() => downloadPdfReport(result)}
                className="btn-ghost"
                style={{ padding: "5px 12px" }}
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export PDF
              </button>
            )}
          </div>
        )}

        {showHero && (
          <div
            className="mb-6 pb-4"
            style={{ borderBottom: "1px solid #1e1e1e" }}
          >
            <span
              className="text-xs uppercase tracking-widest"
              style={{ color: "#d4372c", fontFamily: "DM Mono, monospace" }}
            >
              Analyze an article
            </span>
          </div>
        )}

        <div className="max-w-2xl mx-auto mb-8">
          <InputPanel
            onAnalyze={runAnalysis}
            onCompare={runCompare}
            isLoading={loading}
          />
        </div>

        {/* Loading */}
        <AnimatePresence>
          {loading && <LoadingView stage={stage} />}
        </AnimatePresence>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="max-w-lg mx-auto mb-8"
            >
              <div
                className="panel"
                style={{ borderColor: "rgba(212,55,44,0.4)" }}
              >
                <div className="panel-body flex items-start gap-3">
                  <div
                    className="w-6 h-6 rounded-sm shrink-0 flex items-center justify-center text-xs"
                    style={{ background: "rgba(212,55,44,0.15)", color: "#d4372c" }}
                  >
                    ✕
                  </div>
                  <div>
                    <p
                      className="text-lg leading-relaxed text-[var(--chalk)] mb-4"
                    >
                      <strong className="text-white font-semibold">Analysis failed</strong>
                    </p>
                    <p className="text-base leading-relaxed text-[var(--chalk-muted)] border-t border-[var(--rule-dark)] pt-4">
                      {error}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <div ref={resultsRef}>
          <AnimatePresence>
            {result && mode === "single" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.35 }}
                className="grid grid-cols-1 lg:grid-cols-12 gap-4"
              >
                <div className="lg:col-span-5 space-y-4">
                  <BiasPanel bias={result.bias} />
                  {result.source_credibility && (
                    <CredibilityPanel credibility={result.source_credibility} />
                  )}
                  <EvidencePanel evidence={result.bias.evidence} />
                </div>
                <div className="lg:col-span-7 space-y-4">
                  <SummaryPanel
                    title={result.title}
                    summary={result.summary}
                    language={result.language}
                    sourceUrl={result.source_url}
                  />
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <SentimentPanel sentiment={result.sentiment} />
                    <EntityGraph entities={result.bias.entity_bias_map} />
                  </div>
                  {result.claims && result.claims.length > 0 && (
                    <ClaimsPanel claims={result.claims} />
                  )}
                  <NeutralRewritePanel rewrites={result.neutral_rewrites} />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {compareResult && mode === "compare" && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <CompareView data={compareResult} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer
        className="mt-20"
        style={{ borderTop: "1px solid #1e1e1e" }}
      >
        <div className="max-w-6xl mx-auto px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div
            className="flex items-center gap-4 text-[10px] uppercase tracking-widest"
            style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
          >
            <span style={{ color: "#9a9490" }}>NEWSROOM LENS</span>
            <span>Groq LLaMA</span>
            <span>ModernBERT</span>
            <span>IndicTrans2</span>
            <span>GLiNER</span>
          </div>
          <span
            className="text-[10px] uppercase tracking-widest"
            style={{ color: "#3a3a3a", fontFamily: "DM Mono, monospace" }}
          >
            Zero data leaves your machine
          </span>
        </div>
      </footer>
    </div>
  );
}
