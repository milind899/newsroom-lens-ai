"use client";

import { motion } from "framer-motion";
import { SourceCredibility } from "@/lib/types";

function scoreColor(score: number | null) {
  if (score === null) return "#5a5450";
  if (score >= 80) return "#1e7c4a";
  if (score >= 65) return "#4a9e6e";
  if (score >= 50) return "#d4831c";
  if (score >= 35) return "#d4372c";
  return "#9b1c14";
}

function factualColor(level: string) {
  const l = level.toLowerCase();
  if (l === "very high") return "#1e7c4a";
  if (l === "high") return "#4a9e6e";
  if (l === "mixed") return "#d4831c";
  if (l === "low") return "#d4372c";
  if (l === "very low") return "#9b1c14";
  return "#5a5450";
}

function biasColor(bias: string) {
  const b = bias.toLowerCase();
  if (b === "left") return "#3b82f6";
  if (b === "center-left") return "#60a5fa";
  if (b === "center") return "#8b5cf6";
  if (b === "center-right") return "#f87171";
  if (b === "right") return "#ef4444";
  return "#5a5450";
}

export default function CredibilityPanel({
  credibility,
}: {
  credibility: SourceCredibility;
}) {
  const score = credibility.reliability_score;
  const col = scoreColor(score);

  return (
    <div className="panel animate-fade-up stagger-2">
      <div className="panel-header">
        <div className="w-2 h-2" style={{ background: "#8b5cf6" }} />
        <span className="panel-label">Source Credibility</span>
        {credibility.known && (
          <span
            className="ml-auto text-[10px]"
            style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
          >
            MBFC-style rating
          </span>
        )}
      </div>

      <div className="panel-body">
        {!credibility.known ? (
          <div className="flex items-start gap-3">
            <div
              className="w-6 h-6 shrink-0 flex items-center justify-center text-xs"
              style={{
                background: "rgba(154,148,144,0.1)",
                color: "#5a5450",
              }}
            >
              ?
            </div>
            <div>
              <p
                className="text-sm font-semibold mb-1"
                style={{ color: "#9a9490" }}
              >
                Unknown source
              </p>
              <p className="text-xs" style={{ color: "#5a5450" }}>
                {credibility.description}
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Score + Domain */}
            <div className="flex items-center gap-4">
              {/* Score circle */}
              <div className="relative" style={{ width: 72, height: 72 }}>
                <svg viewBox="0 0 72 72" width="72" height="72">
                  <circle
                    cx="36"
                    cy="36"
                    r="30"
                    fill="none"
                    stroke="#222"
                    strokeWidth="4"
                  />
                  <motion.circle
                    cx="36"
                    cy="36"
                    r="30"
                    fill="none"
                    stroke={col}
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={2 * Math.PI * 30}
                    initial={{ strokeDashoffset: 2 * Math.PI * 30 }}
                    animate={{
                      strokeDashoffset:
                        2 * Math.PI * 30 * (1 - (score || 0) / 100),
                    }}
                    transition={{ duration: 1.2, ease: "easeOut" }}
                    transform="rotate(-90 36 36)"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span
                    className="font-display font-bold text-xl"
                    style={{
                      color: col,
                      fontFamily: "Syne, sans-serif",
                    }}
                  >
                    {score}
                  </span>
                </div>
              </div>

              <div className="flex-1 min-w-0">
                <div
                  className="text-sm font-semibold mb-1 truncate"
                  style={{ color: "#e8e2d8" }}
                >
                  {credibility.domain}
                </div>
                <div
                  className="text-[10px] uppercase tracking-widest mb-1.5"
                  style={{
                    color: "#5a5450",
                    fontFamily: "DM Mono, monospace",
                  }}
                >
                  {credibility.category}
                </div>
                <p className="text-xs leading-relaxed" style={{ color: "#9a9490" }}>
                  {credibility.description}
                </p>
              </div>
            </div>

            {/* Meta badges */}
            <div className="flex flex-wrap gap-2">
              {/* Factual reporting */}
              <div
                style={{
                  background: "#181818",
                  border: "1px solid #2e2e2e",
                  padding: "5px 10px",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: factualColor(credibility.factual_reporting),
                  }}
                />
                <span
                  className="text-[10px] uppercase tracking-wider"
                  style={{
                    color: "#5a5450",
                    fontFamily: "DM Mono, monospace",
                  }}
                >
                  Factual:
                </span>
                <span
                  className="text-xs capitalize"
                  style={{
                    color: factualColor(credibility.factual_reporting),
                  }}
                >
                  {credibility.factual_reporting}
                </span>
              </div>

              {/* Bias rating */}
              <div
                style={{
                  background: "#181818",
                  border: "1px solid #2e2e2e",
                  padding: "5px 10px",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: biasColor(credibility.bias_rating),
                  }}
                />
                <span
                  className="text-[10px] uppercase tracking-wider"
                  style={{
                    color: "#5a5450",
                    fontFamily: "DM Mono, monospace",
                  }}
                >
                  Bias:
                </span>
                <span
                  className="text-xs capitalize"
                  style={{
                    color: biasColor(credibility.bias_rating),
                  }}
                >
                  {credibility.bias_rating}
                </span>
              </div>

              {/* Reliability tier */}
              <div
                style={{
                  background: "#181818",
                  border: "1px solid #2e2e2e",
                  padding: "5px 10px",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: col,
                  }}
                />
                <span
                  className="text-[10px] uppercase tracking-wider"
                  style={{
                    color: "#5a5450",
                    fontFamily: "DM Mono, monospace",
                  }}
                >
                  Reliability:
                </span>
                <span
                  className="text-xs"
                  style={{ color: col }}
                >
                  {score !== null && score >= 80
                    ? "High"
                    : score !== null && score >= 65
                    ? "Above avg"
                    : score !== null && score >= 50
                    ? "Mixed"
                    : score !== null && score >= 35
                    ? "Low"
                    : "Very low"}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
