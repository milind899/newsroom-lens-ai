"use client";

import { useState, useRef } from "react";
import { motion } from "framer-motion";

interface InputPanelProps {
  onAnalyze: (params: { url?: string; text?: string; file?: File; output_language?: string }) => void;
  onCompare: (urlA: string, urlB: string, outputLang: string) => void;
  isLoading: boolean;
}

const TABS = [
  { key: "url" as const, label: "URL" },
  { key: "text" as const, label: "Text" },
  { key: "pdf" as const, label: "PDF" },
  { key: "compare" as const, label: "Compare" },
];

const OUTPUT_LANGUAGES = [
  { code: "en", name: "English" },
  // Indian languages (IndicTrans2 — local, no API calls)
  { code: "hi", name: "Hindi" },
  { code: "bn", name: "Bengali" },
  { code: "ta", name: "Tamil" },
  { code: "te", name: "Telugu" },
  { code: "mr", name: "Marathi" },
  { code: "ur", name: "Urdu" },
  { code: "gu", name: "Gujarati" },
  { code: "kn", name: "Kannada" },
  { code: "ml", name: "Malayalam" },
  { code: "pa", name: "Punjabi" },
  { code: "or", name: "Odia" },
  { code: "as", name: "Assamese" },
  { code: "sa", name: "Sanskrit" },
  { code: "ne", name: "Nepali" },
  { code: "si", name: "Sinhala" },
  { code: "sd", name: "Sindhi" },
  { code: "ks", name: "Kashmiri" },
  { code: "mai", name: "Maithili" },
  { code: "doi", name: "Dogri" },
  { code: "mni", name: "Manipuri" },
  { code: "bodo", name: "Bodo" },
  // International languages (Groq API)
  { code: "fr", name: "French" },
  { code: "es", name: "Spanish" },
  { code: "de", name: "German" },
  { code: "ar", name: "Arabic" },
  { code: "zh", name: "Chinese" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "pt", name: "Portuguese" },
  { code: "ru", name: "Russian" },
];

export default function InputPanel({ onAnalyze, onCompare, isLoading }: InputPanelProps) {
  const [mode, setMode] = useState<"url" | "text" | "pdf" | "compare">("url");
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [urlA, setUrlA] = useState("");
  const [urlB, setUrlB] = useState("");
  const [outputLang, setOutputLang] = useState("en");
  const fileRef = useRef<HTMLInputElement>(null);

  const canSubmit = () => {
    if (isLoading) return false;
    if (mode === "url") return url.trim().length > 0;
    if (mode === "text") return text.trim().length > 0;
    if (mode === "pdf") return file !== null;
    if (mode === "compare") return urlA.trim().length > 0 && urlB.trim().length > 0;
    return false;
  };

  const handleSubmit = () => {
    if (mode === "compare") {
      if (urlA.trim() && urlB.trim()) onCompare(urlA.trim(), urlB.trim(), outputLang);
      return;
    }
    if (mode === "url" && url.trim()) onAnalyze({ url: url.trim(), output_language: outputLang });
    else if (mode === "text" && text.trim()) onAnalyze({ text: text.trim(), output_language: outputLang });
    else if (mode === "pdf" && file) onAnalyze({ file, output_language: outputLang });
  };

  return (
    <div className="panel">
      {/* Tab bar */}
      <div
        className="flex"
        style={{ borderBottom: "1px solid #2e2e2e" }}
      >
        {TABS.map((tab) => {
          const active = mode === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setMode(tab.key)}
              className="relative flex-1 py-3 text-[11px] uppercase tracking-widest transition-colors"
              style={{
                fontFamily: "DM Mono, monospace",
                color: active ? "#e8e2d8" : "#5a5450",
                background: "none",
                border: "none",
                cursor: "pointer",
                borderRight: tab.key !== "compare" ? "1px solid #1e1e1e" : "none",
              }}
            >
              {tab.label}
              {active && (
                <motion.div
                  layoutId="inputTab"
                  className="absolute bottom-0 left-0 right-0 h-[2px]"
                  style={{ background: "#d4372c" }}
                  transition={{ type: "spring", stiffness: 500, damping: 40 }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Body */}
      <div className="panel-body space-y-4">
        {mode === "url" && (
          <div>
            <label
              className="block text-[10px] uppercase tracking-widest mb-2"
              style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
            >
              Article URL
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && canSubmit() && handleSubmit()}
              placeholder="https://www.bbc.com/news/world-..."
              className="input-field"
            />
          </div>
        )}

        {mode === "text" && (
          <div>
            <label
              className="block text-[10px] uppercase tracking-widest mb-2"
              style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
            >
              Article text
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste the full article text here…"
              className="input-field resize-none"
              rows={6}
            />
            <div
              className="text-right mt-1 text-[10px]"
              style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
            >
              {text.split(/\s+/).filter(Boolean).length} words
            </div>
          </div>
        )}

        {mode === "pdf" && (
          <div>
            <label
              className="block text-[10px] uppercase tracking-widest mb-2"
              style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
            >
              PDF document
            </label>
            <div
              onClick={() => fileRef.current?.click()}
              className="cursor-pointer flex flex-col items-center justify-center gap-2 p-8 transition-colors"
              style={{
                border: `1px dashed ${file ? "#1e7c4a" : "#3a3a3a"}`,
                borderRadius: 2,
                background: file ? "rgba(30,124,74,0.04)" : "transparent",
              }}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".pdf"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              {file ? (
                <>
                  <span style={{ color: "#1e7c4a", fontSize: 22 }}>✓</span>
                  <span className="text-sm" style={{ color: "#e8e2d8" }}>
                    {file.name}
                  </span>
                  <span
                    className="text-[10px]"
                    style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
                  >
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                </>
              ) : (
                <>
                  <svg
                    className="w-7 h-7"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="#3a3a3a"
                    strokeWidth={1.5}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  <span className="text-sm" style={{ color: "#9a9490" }}>
                    Click to upload
                  </span>
                  <span
                    className="text-[10px]"
                    style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
                  >
                    PDF — up to 10 MB
                  </span>
                </>
              )}
            </div>
          </div>
        )}

        {mode === "compare" && (
          <div className="space-y-3">
            <p className="text-sm" style={{ color: "#5a5450" }}>
              Compare how two outlets frame the same story.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label
                  className="block text-[10px] uppercase tracking-widest mb-2"
                  style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
                >
                  <span style={{ color: "#3b82f6" }}>◆</span> Source A
                </label>
                <input
                  type="url"
                  value={urlA}
                  onChange={(e) => setUrlA(e.target.value)}
                  placeholder="https://source-one.com/…"
                  className="input-field"
                />
              </div>
              <div>
                <label
                  className="block text-[10px] uppercase tracking-widest mb-2"
                  style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
                >
                  <span style={{ color: "#ef4444" }}>◆</span> Source B
                </label>
                <input
                  type="url"
                  value={urlB}
                  onChange={(e) => setUrlB(e.target.value)}
                  placeholder="https://source-two.com/…"
                  className="input-field"
                />
              </div>
            </div>
          </div>
        )}

        {/* Output language selector — shown in all modes */}
        <div className="flex items-center gap-3">
          <label
            className="text-[10px] uppercase tracking-widest shrink-0"
            style={{ color: "#5a5450", fontFamily: "DM Mono, monospace" }}
          >
            Output language
          </label>
          <select
            value={outputLang}
            onChange={(e) => setOutputLang(e.target.value)}
            className="input-field flex-1"
            style={{
              padding: "6px 10px",
              fontSize: 13,
              appearance: "auto",
            }}
          >
            {OUTPUT_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleSubmit}
          disabled={!canSubmit()}
          className="btn-primary w-full"
        >
          {isLoading ? (
            <>
              <div
                className="w-3 h-3 rounded-full border-2 animate-spin"
                style={{ borderColor: "rgba(255,255,255,0.2)", borderTopColor: "white" }}
              />
              Processing…
            </>
          ) : mode === "compare" ? (
            "Compare sources"
          ) : (
            "Analyze article"
          )}
        </button>
      </div>
    </div>
  );
}
