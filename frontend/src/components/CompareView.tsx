"use client";

import { motion } from "framer-motion";
import { CompareResponse } from "@/lib/types";

function getBiasColor(v: number) {
  if (v < 25) return "#1e7c4a";
  if (v < 50) return "#d4831c";
  if (v < 75) return "#d4372c";
  return "#9b1c14";
}

function MiniGauge({ value, label }: { value: number; label: string }) {
  const R = 36;
  const circ = 2 * Math.PI * R;
  const arc = circ * 0.75;
  const filled = (value / 100) * arc;
  const color = getBiasColor(value);

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
      <div style={{ position: "relative", width: 96, height: 96 }}>
        <svg viewBox="0 0 90 90" width="96" height="96">
          <circle
            cx="45" cy="45" r={R}
            fill="none" stroke="#222" strokeWidth="6"
            strokeDasharray={`${arc} ${circ - arc}`}
            strokeLinecap="round"
            transform="rotate(135 45 45)"
          />
          <motion.circle
            cx="45" cy="45" r={R}
            fill="none" stroke={color} strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={`${arc} ${circ - arc}`}
            initial={{ strokeDashoffset: arc }}
            animate={{ strokeDashoffset: arc - filled }}
            transition={{ duration: 1.1, ease: "easeOut" }}
            transform="rotate(135 45 45)"
          />
        </svg>
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span
            style={{
              fontFamily: "Syne, sans-serif",
              fontWeight: 800,
              fontSize: 26,
              color,
              lineHeight: 1,
            }}
          >
            {Math.round(value)}
          </span>
        </div>
      </div>
      <span
        className="text-[10px] uppercase tracking-widest"
        style={{
          color: "#9a9490",
          fontFamily: "DM Mono, monospace",
          maxWidth: 110,
          textAlign: "center",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </span>
    </div>
  );
}

export default function CompareView({ data }: { data: CompareResponse }) {
  const getDomain = (url: string | null) => {
    if (!url) return "Source";
    try { return new URL(url).hostname.replace("www.", ""); } catch { return "Source"; }
  };

  const domA = getDomain(data.source_a.source_url);
  const domB = getDomain(data.source_b.source_url);

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Overview */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-label">Comparison Overview</span>
        </div>
        <div className="panel-body">
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr auto 1fr",
              alignItems: "center",
              gap: 24,
            }}
          >
            <MiniGauge value={data.source_a.bias.bias_index} label={domA} />
            <div style={{ textAlign: "center" }}>
              <motion.div
                style={{
                  fontFamily: "Syne, sans-serif",
                  fontWeight: 800,
                  fontSize: 36,
                  color: "#e8e2d8",
                  lineHeight: 1,
                }}
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 }}
              >
                {data.bias_index_delta.toFixed(1)}
              </motion.div>
              <div
                className="text-[10px] uppercase tracking-widest mt-1"
                style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
              >
                Bias delta
              </div>
              <div
                className="text-[10px] mt-2"
                style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
              >
                Sentiment gap:{" "}
                <span style={{ color: "#9a9490" }}>
                  {(data.sentiment_delta * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <MiniGauge value={data.source_b.bias.bias_index} label={domB} />
          </div>
        </div>
      </div>

      {/* Bias type overlap / divergence */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="panel">
          <div className="panel-header">
            <span className="panel-label">Shared bias types</span>
          </div>
          <div className="panel-body">
            {data.bias_type_overlap.length > 0 ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {data.bias_type_overlap.map((t) => (
                  <span
                    key={t}
                    className="badge"
                    style={{
                      background: "rgba(212,131,28,0.1)",
                      color: "#d4831c",
                      border: "1px solid rgba(212,131,28,0.2)",
                    }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm" style={{ color: "#5a5450" }}>
                No overlapping bias types
              </p>
            )}
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <span className="panel-label">Unique bias types</span>
          </div>
          <div className="panel-body">
            {Object.keys(data.bias_type_divergence).length > 0 ? (
              <div className="space-y-2">
                {Object.entries(data.bias_type_divergence).map(([type, source]) => (
                  <div
                    key={type}
                    style={{ display: "flex", justifyContent: "space-between" }}
                  >
                    <span className="text-sm" style={{ color: "#e8e2d8" }}>
                      {type}
                    </span>
                    <span
                      className="text-[10px]"
                      style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
                    >
                      {source}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm" style={{ color: "#5a5450" }}>
                No unique bias types
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Entity framing table */}
      {data.entity_framing_comparison.length > 0 && (
        <div className="panel">
          <div className="panel-header">
            <span className="panel-label">Entity framing</span>
          </div>
          {data.entity_framing_comparison.map((ent, i) => (
            <div
              key={i}
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: 12,
                padding: "10px 20px",
                borderBottom:
                  i < data.entity_framing_comparison.length - 1
                    ? "1px solid #1e1e1e"
                    : "none",
                alignItems: "center",
              }}
            >
              <div style={{ textAlign: "center" }}>
                <div
                  className="text-[9px] uppercase tracking-widest mb-1"
                  style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
                >
                  {domA}
                </div>
                <span
                  className="text-xs capitalize"
                  style={{
                    color:
                      ent.source_a_sentiment === "neutral" ? "#9a9490" : "#d4372c",
                  }}
                >
                  {ent.source_a_sentiment}
                </span>
              </div>
              <div style={{ textAlign: "center" }}>
                <span className="text-sm font-semibold" style={{ color: "#e8e2d8" }}>
                  {ent.entity}
                </span>
              </div>
              <div style={{ textAlign: "center" }}>
                <div
                  className="text-[9px] uppercase tracking-widest mb-1"
                  style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
                >
                  {domB}
                </div>
                <span
                  className="text-xs capitalize"
                  style={{
                    color:
                      ent.source_b_sentiment === "neutral" ? "#9a9490" : "#d4372c",
                  }}
                >
                  {ent.source_b_sentiment}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Side-by-side summaries */}
      <div className="grid md:grid-cols-2 gap-4">
        {[
          { label: domA, src: data.source_a },
          { label: domB, src: data.source_b },
        ].map(({ label, src }) => (
          <div key={label} className="panel">
            <div className="panel-header">
              <span className="panel-label">{label}</span>
            </div>
            <div className="panel-body">
              <h3
                className="text-sm font-semibold mb-3 leading-snug"
                style={{ color: "#e8e2d8", fontFamily: "Syne, sans-serif" }}
              >
                {src.title}
              </h3>
              <div className="space-y-2">
                {src.summary.map((s, i) => (
                  <div key={i} style={{ display: "flex", gap: 10 }}>
                    <span
                      style={{
                        color: "#d4372c",
                        fontFamily: "DM Mono, monospace",
                        fontSize: 10,
                        flexShrink: 0,
                        marginTop: 2,
                      }}
                    >
                      {i + 1}
                    </span>
                    <p className="text-xs leading-relaxed" style={{ color: "#9a9490" }}>
                      {s}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
