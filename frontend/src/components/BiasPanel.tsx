"use client";

import { motion } from "framer-motion";
import { BiasResult } from "@/lib/types";

interface BiasPanelProps {
  bias: BiasResult;
}

function getBiasColor(v: number) {
  if (v < 25) return "#22c55e";
  if (v < 50) return "#eab308";
  if (v < 75) return "#ef4444";
  return "#dc2626";
}

function getBiasLabel(v: number) {
  if (v < 20) return "Minimal";
  if (v < 40) return "Low";
  if (v < 60) return "Moderate";
  if (v < 80) return "High";
  return "Severe";
}

function getBiasBg(v: number) {
  if (v < 25) return "rgba(34,197,94,0.08)";
  if (v < 50) return "rgba(234,179,8,0.08)";
  if (v < 75) return "rgba(239,68,68,0.08)";
  return "rgba(220,38,38,0.1)";
}

/* ── Score Card ────────────────────────────────────────────── */
function BiasScore({ value }: { value: number }) {
  const color = getBiasColor(value);
  const label = getBiasLabel(value);
  const pct = Math.min(value, 100);

  return (
    <div
      className="flex flex-col items-center justify-center p-5"
      style={{
        background: getBiasBg(value),
        border: `1px solid ${color}20`,
        borderRadius: 4,
      }}
    >
      <motion.div
        className="font-display leading-none"
        style={{
          fontFamily: "Syne, sans-serif",
          fontWeight: 800,
          fontSize: 52,
          color,
          lineHeight: 1,
        }}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        {Math.round(value)}
      </motion.div>
      <span
        className="text-[10px] mt-1 uppercase tracking-widest"
        style={{ color: "#6b6560", fontFamily: "DM Mono, monospace" }}
      >
        / 100
      </span>

      {/* Horizontal bar */}
      <div
        className="w-full mt-3 overflow-hidden"
        style={{ height: 4, background: "#1a1a1a", borderRadius: 2 }}
      >
        <motion.div
          style={{ height: "100%", background: color, borderRadius: 2 }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>

      <motion.span
        className="text-[11px] uppercase tracking-widest mt-2 font-semibold"
        style={{ color, fontFamily: "DM Mono, monospace" }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        {label} Bias
      </motion.span>
    </div>
  );
}

/* ── Political Leaning ────────────────────────────────────── */
function LeaningBar({ leaning }: { leaning: { label: string; confidence: number } }) {
  const label = leaning.label.toLowerCase();
  const pct =
    label === "left" ? 10
    : label === "center-left" ? 30
    : label === "center" ? 50
    : label === "center-right" ? 70
    : label === "right" ? 90
    : 50;

  const markerColor =
    pct < 35 ? "#3b82f6" : pct > 65 ? "#ef4444" : "#a78bfa";

  return (
    <div>
      <div className="flex justify-between mb-1">
        {["Left", "Center", "Right"].map((l) => (
          <span
            key={l}
            className="text-[9px] uppercase tracking-widest"
            style={{
              fontFamily: "DM Mono, monospace",
              color:
                l === "Left" ? "#3b82f6" : l === "Right" ? "#ef4444" : "#a78bfa",
              opacity: 0.7,
            }}
          >
            {l}
          </span>
        ))}
      </div>
      <div
        className="relative overflow-visible"
        style={{
          height: 6,
          background: "linear-gradient(to right, #1e3a5f, #2d1b4e, #5f1e1e)",
          borderRadius: 3,
        }}
      >
        {/* Subtle segment markers */}
        <div className="absolute top-0 bottom-0 left-1/3" style={{ width: 1, background: "#ffffff10" }} />
        <div className="absolute top-0 bottom-0 left-2/3" style={{ width: 1, background: "#ffffff10" }} />

        <motion.div
          className="absolute"
          style={{
            top: "50%",
            width: 12,
            height: 12,
            borderRadius: 2,
            transform: "translateY(-50%) rotate(45deg)",
            background: markerColor,
            marginLeft: -6,
            boxShadow: `0 0 8px ${markerColor}40`,
          }}
          initial={{ left: "50%" }}
          animate={{ left: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.3 }}
        />
      </div>
      <p
        className="text-center text-[11px] mt-2"
        style={{ color: "#9a9490", fontFamily: "DM Mono, monospace" }}
      >
        <span style={{ color: "#e8e2d8", fontWeight: 600 }}>{leaning.label}</span>
        <span style={{ color: "#4a4540", margin: "0 4px" }}>|</span>
        {Math.round(leaning.confidence * 100)}%
      </p>
    </div>
  );
}

/* ── Signal Bar ───────────────────────────────────────────── */
function SignalRow({ label, value, delay }: { label: string; value: number; delay: number }) {
  const color = value < 30 ? "#22c55e" : value < 60 ? "#eab308" : "#ef4444";
  const displayLabel = label
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="flex items-center gap-3">
      <span
        className="text-[10px] uppercase tracking-wider w-32 shrink-0 text-right"
        style={{ color: "#6b6560", fontFamily: "DM Mono, monospace" }}
      >
        {displayLabel}
      </span>
      <div className="flex-1 relative" style={{ height: 6, background: "#161616", borderRadius: 3 }}>
        <motion.div
          className="absolute inset-y-0 left-0"
          style={{ background: color, borderRadius: 3 }}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8, ease: "easeOut", delay }}
        />
      </div>
      <span
        className="text-[10px] w-8 text-right shrink-0 font-medium"
        style={{ color, fontFamily: "DM Mono, monospace" }}
      >
        {Math.round(value)}
      </span>
    </div>
  );
}

/* ── Main Panel ───────────────────────────────────────────── */
export default function BiasPanel({ bias }: BiasPanelProps) {
  const topTypes = bias.bias_types
    .filter((b) => !["no bias", "unbiased", "none"].includes(b.bias_type.toLowerCase()))
    .filter((b) => b.confidence > 0.10)
    .slice(0, 8);

  return (
    <div className="panel animate-fade-up">
      <div className="panel-header">
        <div className="w-2 h-2" style={{ background: getBiasColor(bias.bias_index), borderRadius: 1 }} />
        <span className="panel-label">Bias Analysis</span>
        <span
          className="ml-auto text-[10px]"
          style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
        >
          {Math.round(bias.bias_index)}/100
        </span>
      </div>

      <div className="panel-body space-y-5">
        {/* Score + Leaning side by side */}
        <div className="grid grid-cols-2 gap-5">
          <BiasScore value={bias.bias_index} />
          <div className="flex flex-col justify-center">
            <div
              className="text-[10px] uppercase tracking-widest mb-3"
              style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
            >
              Political Leaning
            </div>
            <LeaningBar leaning={bias.political_leaning} />
          </div>
        </div>

        {/* Detected bias types */}
        {topTypes.length > 0 && (
          <div>
            <div
              className="text-[10px] uppercase tracking-widest mb-2.5"
              style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
            >
              Detected Bias Types
            </div>
            <div className="flex flex-wrap gap-1.5">
              {topTypes.map((bt, i) => {
                const pct = Math.round(bt.confidence * 100);
                const col = pct > 70 ? "#ef4444" : pct > 40 ? "#eab308" : "#22c55e";
                return (
                  <motion.div
                    key={bt.bias_type}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05 * i }}
                    className="flex items-center gap-1.5"
                    style={{
                      background: "#141414",
                      border: "1px solid #222",
                      padding: "4px 8px",
                      borderRadius: 2,
                      borderLeft: `2px solid ${col}`,
                    }}
                  >
                    <span className="text-[12px]" style={{ color: "#d4d0cc" }}>
                      {bt.bias_type}
                    </span>
                    <span
                      className="text-[9px] font-medium"
                      style={{ color: col, fontFamily: "DM Mono, monospace" }}
                    >
                      {pct}%
                    </span>
                  </motion.div>
                );
              })}
            </div>
          </div>
        )}

        {/* Signal breakdown */}
        <div>
          <div
            className="text-[10px] uppercase tracking-widest mb-2.5"
            style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
          >
            Signal Breakdown
          </div>
          <div className="space-y-2">
            {Object.entries(bias.bias_breakdown).map(([k, v], i) => (
              <SignalRow key={k} label={k} value={v} delay={0.1 * i} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
