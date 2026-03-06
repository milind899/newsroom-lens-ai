"use client";

import { motion } from "framer-motion";
import { ClaimVerification } from "@/lib/types";

const VERDICT_META: Record<
  string,
  { color: string; bg: string; border: string; icon: string }
> = {
  verified: {
    color: "#1e7c4a",
    bg: "rgba(30,124,74,0.08)",
    border: "rgba(30,124,74,0.25)",
    icon: "✓",
  },
  unverified: {
    color: "#d4831c",
    bg: "rgba(212,131,28,0.08)",
    border: "rgba(212,131,28,0.25)",
    icon: "?",
  },
  misleading: {
    color: "#d4372c",
    bg: "rgba(212,55,44,0.08)",
    border: "rgba(212,55,44,0.25)",
    icon: "!",
  },
  opinion: {
    color: "#8b5cf6",
    bg: "rgba(139,92,246,0.08)",
    border: "rgba(139,92,246,0.25)",
    icon: "~",
  },
};

function ClaimCard({
  claim,
  index,
}: {
  claim: ClaimVerification;
  index: number;
}) {
  const meta = VERDICT_META[claim.verdict] || VERDICT_META.unverified;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.08 * index }}
      style={{
        background: "#0d0d0d",
        border: "1px solid #2e2e2e",
        padding: 0,
        overflow: "hidden",
      }}
    >
      {/* Verdict strip */}
      <div
        style={{
          height: 2,
          background: meta.color,
        }}
      />

      <div style={{ padding: "12px 14px" }}>
        {/* Verdict badge */}
        <div className="flex items-center gap-2 mb-2">
          <div
            style={{
              width: 18,
              height: 18,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 10,
              fontWeight: 700,
              fontFamily: "DM Mono, monospace",
              background: meta.bg,
              color: meta.color,
              border: `1px solid ${meta.border}`,
            }}
          >
            {meta.icon}
          </div>
          <span
            className="text-[10px] uppercase tracking-widest font-medium"
            style={{
              color: meta.color,
              fontFamily: "DM Mono, monospace",
            }}
          >
            {claim.verdict}
          </span>
        </div>

        {/* Claim text */}
        <p
          className="text-sm leading-relaxed mb-2"
          style={{ color: "#e8e2d8" }}
        >
          {claim.claim}
        </p>

        {/* Explanation */}
        {claim.explanation && (
          <p
            className="text-xs leading-relaxed"
            style={{ color: "#5a5450" }}
          >
            {claim.explanation}
          </p>
        )}
      </div>
    </motion.div>
  );
}

export default function ClaimsPanel({
  claims,
}: {
  claims: ClaimVerification[];
}) {
  if (!claims || claims.length === 0) return null;

  const counts = {
    verified: claims.filter((c) => c.verdict === "verified").length,
    unverified: claims.filter((c) => c.verdict === "unverified").length,
    misleading: claims.filter((c) => c.verdict === "misleading").length,
    opinion: claims.filter((c) => c.verdict === "opinion").length,
  };

  return (
    <div className="panel animate-fade-up stagger-4">
      <div className="panel-header">
        <div className="w-2 h-2" style={{ background: "#d4831c" }} />
        <span className="panel-label">Claim Verification</span>
        <span
          className="ml-auto text-[10px]"
          style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
        >
          {claims.length} claims analyzed
        </span>
      </div>

      <div className="panel-body space-y-4">
        {/* Verdict summary bar */}
        <div className="flex gap-3">
          {(
            [
              ["verified", counts.verified],
              ["unverified", counts.unverified],
              ["misleading", counts.misleading],
              ["opinion", counts.opinion],
            ] as [string, number][]
          )
            .filter(([, n]) => n > 0)
            .map(([verdict, n]) => {
              const meta = VERDICT_META[verdict];
              return (
                <div
                  key={verdict}
                  className="flex items-center gap-1.5"
                  style={{
                    background: meta.bg,
                    border: `1px solid ${meta.border}`,
                    padding: "3px 8px",
                  }}
                >
                  <div
                    style={{
                      width: 5,
                      height: 5,
                      borderRadius: "50%",
                      background: meta.color,
                    }}
                  />
                  <span
                    className="text-[10px] uppercase tracking-wider"
                    style={{
                      color: meta.color,
                      fontFamily: "DM Mono, monospace",
                    }}
                  >
                    {verdict} ({n})
                  </span>
                </div>
              );
            })}
        </div>

        {/* Claim cards */}
        <div className="space-y-2">
          {claims.map((claim, i) => (
            <ClaimCard key={i} claim={claim} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
