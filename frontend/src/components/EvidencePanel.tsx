"use client";

import { motion } from "framer-motion";
import { BiasEvidence } from "@/lib/types";

export default function EvidencePanel({ evidence }: { evidence: BiasEvidence[] }) {
  const empty = !evidence || evidence.length === 0;

  return (
    <div className="panel animate-fade-up stagger-2">
      <div className="panel-header" style={{ justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div className="w-2 h-2" style={{ background: "#d4372c" }} />
          <span className="panel-label">Bias Evidence</span>
        </div>
        {!empty && (
          <span
            className="text-[10px]"
            style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
          >
            {evidence.length} flagged
          </span>
        )}
      </div>

      {empty ? (
        <div className="panel-body">
          <p className="text-sm" style={{ color: "#5a5450" }}>
            No significant bias detected in individual sentences.
          </p>
        </div>
      ) : (
        <div>
          {evidence.map((ev, i) => {
            const pct = Math.round(ev.confidence * 100);
            const col = pct > 70 ? "#d4372c" : pct > 40 ? "#d4831c" : "#1e7c4a";
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + i * 0.07 }}
                style={{
                  borderBottom: "1px solid #1e1e1e",
                  padding: "14px 20px",
                }}
              >
                <div style={{ display: "flex", gap: 12 }}>
                  <div
                    style={{ width: 2, background: col, borderRadius: 1, flexShrink: 0 }}
                  />
                  <div style={{ flex: 1 }}>
                    <p
                      className="text-sm leading-relaxed mb-2"
                      style={{ color: "#9a9490", fontStyle: "italic" }}
                    >
                      &ldquo;{ev.sentence}&rdquo;
                    </p>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span
                        className="badge"
                        style={{
                          background: `${col}18`,
                          color: col,
                          border: `1px solid ${col}30`,
                        }}
                      >
                        {ev.bias_type}
                      </span>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <div
                          style={{
                            width: 52,
                            height: 3,
                            background: "#222",
                            overflow: "hidden",
                          }}
                        >
                          <div
                            style={{ width: `${pct}%`, height: "100%", background: col }}
                          />
                        </div>
                        <span
                          className="text-[10px]"
                          style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
                        >
                          {pct}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
