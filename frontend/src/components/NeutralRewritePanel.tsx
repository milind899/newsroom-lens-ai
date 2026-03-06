"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { NeutralRewrite } from "@/lib/types";

export default function NeutralRewritePanel({ rewrites }: { rewrites: NeutralRewrite[] }) {
  const [showNeutral, setShowNeutral] = useState(false);
  if (!rewrites || rewrites.length === 0) return null;

  return (
    <div className="panel animate-fade-up stagger-5">
      <div className="panel-header" style={{ justifyContent: "space-between" }}>
        <span className="panel-label">Neutral Rewrites</span>
        <button
          onClick={() => setShowNeutral((v) => !v)}
          className={`btn-ghost ${showNeutral ? "active" : ""}`}
        >
          {showNeutral ? "← Biased" : "Neutral →"}
        </button>
      </div>

      <div>
        {rewrites.map((rw, i) => (
          <div
            key={i}
            style={{
              borderBottom: i < rewrites.length - 1 ? "1px solid #1e1e1e" : "none",
              padding: "14px 20px",
            }}
          >
            <span
              className="badge mb-3 inline-block"
              style={{
                background: "rgba(212,55,44,0.1)",
                color: "#d4372c",
                border: "1px solid rgba(212,55,44,0.15)",
              }}
            >
              {rw.bias_type}
            </span>

            <AnimatePresence mode="wait">
              {showNeutral ? (
                <motion.div
                  key="neutral"
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.18 }}
                  style={{ display: "flex", gap: 12 }}
                >
                  <div
                    style={{
                      width: 2,
                      background: "#1e7c4a",
                      flexShrink: 0,
                      borderRadius: 1,
                    }}
                  />
                  <p className="text-sm leading-relaxed" style={{ color: "#4ade80" }}>
                    {rw.neutral}
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  key="original"
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.18 }}
                  style={{ display: "flex", gap: 12 }}
                >
                  <div
                    style={{
                      width: 2,
                      background: "#d4372c",
                      flexShrink: 0,
                      borderRadius: 1,
                    }}
                  />
                  <p
                    className="text-sm leading-relaxed"
                    style={{ color: "#9a9490", fontStyle: "italic" }}
                  >
                    &ldquo;{rw.original}&rdquo;
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </div>
  );
}
