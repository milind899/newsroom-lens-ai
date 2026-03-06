"use client";

import { motion } from "framer-motion";
import { EntityBias } from "@/lib/types";

const TYPE_COLORS: Record<string, string> = {
  person: "#3b82f6",
  organization: "#d4831c",
  country: "#1e7c4a",
  "political party": "#d4372c",
  politician: "#8b5cf6",
};

export default function EntityGraph({ entities }: { entities: EntityBias[] }) {
  const empty = !entities || entities.length === 0;

  return (
    <div className="panel animate-fade-up stagger-4">
      <div className="panel-header">
        <span className="panel-label">Entity Map</span>
        {!empty && (
          <span
            className="ml-auto text-[10px]"
            style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
          >
            {entities.length} entities
          </span>
        )}
      </div>

      {empty ? (
        <div className="panel-body">
          <p className="text-sm" style={{ color: "#5a5450" }}>
            No entity-bias associations detected.
          </p>
        </div>
      ) : (
        <div className="panel-body space-y-2">
          {entities.map((ent, i) => {
            const col = TYPE_COLORS[ent.entity_type.toLowerCase()] || "#9a9490";
            const biased = ent.co_occurring_bias.length > 0;

            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.07 * i }}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 10,
                  padding: "8px 10px",
                  background: "#0d0d0d",
                  border: "1px solid #1e1e1e",
                }}
              >
                {/* Initial avatar */}
                <div
                  style={{
                    width: 28,
                    height: 28,
                    background: `${col}18`,
                    color: col,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: 12,
                    flexShrink: 0,
                    fontFamily: "DM Mono, monospace",
                  }}
                >
                  {ent.entity.charAt(0).toUpperCase()}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                    <span className="text-sm font-medium truncate" style={{ color: "#e8e2d8" }}>
                      {ent.entity}
                    </span>
                    <span
                      style={{
                        background: `${col}15`,
                        color: col,
                        fontFamily: "DM Mono, monospace",
                        fontSize: 9,
                        letterSpacing: "0.1em",
                        textTransform: "uppercase",
                        padding: "1px 5px",
                      }}
                    >
                      {ent.entity_type}
                    </span>
                  </div>
                  {biased ? (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                      {ent.co_occurring_bias.map((b, j) => (
                        <span
                          key={j}
                          style={{
                            background: "rgba(212,55,44,0.1)",
                            color: "#d4372c",
                            border: "1px solid rgba(212,55,44,0.2)",
                            fontFamily: "DM Mono, monospace",
                            fontSize: 9,
                            letterSpacing: "0.08em",
                            padding: "1px 5px",
                          }}
                        >
                          {b}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p
                      className="text-[10px] mt-1"
                      style={{ color: "#3a3a3a", fontFamily: "DM Mono, monospace" }}
                    >
                      No bias association
                    </p>
                  )}
                </div>

                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: biased ? "#d4372c" : "#1e7c4a",
                    flexShrink: 0,
                    marginTop: 3,
                  }}
                />
              </motion.div>
            );
          })}

          {/* Legend */}
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "8px 16px",
              paddingTop: 10,
              borderTop: "1px solid #1e1e1e",
              marginTop: 8,
            }}
          >
            {Object.entries(TYPE_COLORS).map(([type, col]) => (
              <div key={type} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <div
                  style={{ width: 6, height: 6, borderRadius: "50%", background: col }}
                />
                <span
                  className="text-[9px] uppercase tracking-widest capitalize"
                  style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
                >
                  {type}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
