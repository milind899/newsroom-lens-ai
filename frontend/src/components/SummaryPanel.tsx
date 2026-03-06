"use client";

import { motion } from "framer-motion";

interface SummaryPanelProps {
  title: string;
  summary: string[];
  language: {
    detected_language: string;
    language_code: string;
    confidence: number;
    was_translated: boolean;
    is_indian?: boolean;
    translation_method?: string;
  };
  sourceUrl: string | null;
}

export default function SummaryPanel({ title, summary, language, sourceUrl }: SummaryPanelProps) {
  return (
    <div className="panel animate-fade-up stagger-1">
      <div className="panel-header" style={{ justifyContent: "space-between" }}>
        <span className="panel-label">Summary</span>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span
            className="badge"
            style={{
              background: "#222",
              color: "#9a9490",
              border: "1px solid #2e2e2e",
            }}
          >
            {language.detected_language}
          </span>
          {language.is_indian && (
            <span
              className="badge"
              style={{
                background: "#1a1a1a",
                color: "#7c7c7c",
                border: "1px solid #2e2e2e",
                fontFamily: "DM Mono, monospace",
                fontSize: 9,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Indic
            </span>
          )}
          {language.was_translated && language.translation_method === "indictrans2" && (
            <span
              className="badge"
              style={{
                background: "rgba(30,124,74,0.12)",
                color: "#4ade80",
                border: "1px solid rgba(30,124,74,0.25)",
                fontFamily: "DM Mono, monospace",
                fontSize: 9,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              IndicTrans2
            </span>
          )}
          {language.was_translated && language.translation_method === "groq" && (
            <span
              className="badge"
              style={{
                background: "rgba(26,79,212,0.12)",
                color: "#60a5fa",
                border: "1px solid rgba(26,79,212,0.2)",
                fontFamily: "DM Mono, monospace",
                fontSize: 9,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Groq API
            </span>
          )}
        </div>
      </div>

      <div className="panel-body">
        <h2
          className="font-display leading-snug mb-1"
          style={{
            fontFamily: "Syne, sans-serif",
            fontSize: "1.25rem",
            fontWeight: 700,
            color: "#e8e2d8",
          }}
        >
          {title}
        </h2>

        {sourceUrl && (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 mb-5 text-[10px] uppercase tracking-widest transition-colors"
            style={{ color: "#5a5450", fontFamily: "DM Mono, monospace", textDecoration: "none" }}
            onMouseEnter={(e) => ((e.target as HTMLElement).style.color = "#d4372c")}
            onMouseLeave={(e) => ((e.target as HTMLElement).style.color = "#5a5450")}
          >
            ↗ {sourceUrl}
          </a>
        )}

        <div style={{ marginTop: sourceUrl ? 0 : 20 }}>
          {summary.map((bullet, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 + i * 0.07 }}
              style={{
                display: "flex",
                gap: 16,
                padding: "11px 0",
                borderBottom: i < summary.length - 1 ? "1px solid #1e1e1e" : "none",
              }}
            >
              <span
                className="shrink-0"
                style={{
                  color: "#d4372c",
                  fontFamily: "DM Mono, monospace",
                  fontSize: 11,
                  marginTop: 2,
                  width: 18,
                  textAlign: "right",
                }}
              >
                {i + 1}
              </span>
              <p className="text-sm leading-relaxed" style={{ color: "#e8e2d8" }}>
                {bullet}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
