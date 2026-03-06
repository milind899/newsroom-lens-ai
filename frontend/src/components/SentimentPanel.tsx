"use client";

import { motion } from "framer-motion";
import { SentimentComparison } from "@/lib/types";

function sentimentColor(label: string) {
  const l = label.toLowerCase();
  if (l.includes("negative") || l === "1 star" || l === "2 stars") return "#d4372c";
  if (l === "neutral" || l === "3 stars") return "#9a9490";
  return "#1e7c4a";
}

export default function SentimentPanel({ sentiment }: { sentiment: SentimentComparison }) {
  const gapPct = Math.round(sentiment.sentiment_gap * 100);
  const hCol = sentimentColor(sentiment.headline.label);
  const bCol = sentimentColor(sentiment.body.label);

  return (
    <div className="panel animate-fade-up stagger-3">
      <div className="panel-header" style={{ justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div className="w-2 h-2" style={{ background: "#1a4fd4" }} />
          <span className="panel-label">Sentiment</span>
        </div>
        {sentiment.sensationalism_flag && (
          <span
            className="badge"
            style={{
              background: "rgba(212,131,28,0.12)",
              color: "#d4831c",
              border: "1px solid rgba(212,131,28,0.2)",
            }}
          >
            Sensationalism
          </span>
        )}
      </div>

      <div className="panel-body space-y-5">
        {/* Headline vs Body */}
        <div className="grid grid-cols-2 gap-3">
          {[
            { title: "Headline", result: sentiment.headline, col: hCol },
            { title: "Body", result: sentiment.body, col: bCol },
          ].map(({ title, result, col }) => (
            <div
              key={title}
              style={{ background: "#0d0d0d", border: "1px solid #2e2e2e", padding: 12 }}
            >
              <div
                className="text-[10px] uppercase tracking-widest mb-2"
                style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
              >
                {title}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: col,
                    boxShadow: `0 0 6px ${col}60`,
                    flexShrink: 0,
                  }}
                />
                <div>
                  <span
                    className="text-sm font-medium capitalize block"
                    style={{ color: "#e8e2d8" }}
                  >
                    {result.label}
                  </span>
                  <span
                    className="text-[10px]"
                    style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
                  >
                    {Math.round(result.score * 100)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Tone gap */}
        <div>
          <div
            style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}
          >
            <span
              className="text-[10px] uppercase tracking-widest"
              style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
            >
              Tone consistency
            </span>
            <span
              className="text-[10px]"
              style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
            >
              {gapPct}% gap
            </span>
          </div>
          <div style={{ height: 3, background: "#222", overflow: "hidden" }}>
            <motion.div
              style={{
                height: "100%",
                background: sentiment.sensationalism_flag ? "#d4831c" : "#1e7c4a",
                transformOrigin: "left",
              }}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: Math.min(gapPct, 100) / 100 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            />
          </div>
          {sentiment.sensationalism_flag && (
            <p
              className="text-xs mt-2 leading-relaxed"
              style={{ color: "#d4831c" }}
            >
              Headline tone differs significantly from body — possible sensationalized framing.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
