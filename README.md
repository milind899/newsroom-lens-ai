# Lexo — AI-Powered Multilingual News Bias Detector

Lexo analyzes news articles for hidden bias, political leaning, and sentiment manipulation. Paste a URL, raw text, or upload a PDF — Lexo extracts the content, detects the language, translates if needed, then runs a multi-model pipeline to surface exactly *where* and *how* the article is biased.

Built for hackathon judging. Runs entirely on consumer hardware (RTX 3050, 16 GB RAM).

---

## What It Does

| Step | What happens | Model / tool |
|------|-------------|--------------|
| **Extract** | Pulls article text from URL, pasted text, or PDF | newspaper3k + trafilatura + readability-lxml + PyMuPDF |
| **Language** | Detects language (38+ languages) | lingua-language-detector |
| **Translate** | Translates non-English articles to English | NLLB-200-distilled-600M (local, on GPU) |
| **Sentiment** | Headline vs. body sentiment comparison, sensationalism flag | HuggingFace sentiment pipeline (local) |
| **Bias classify** | Detects bias types: political, racial, gender, socioeconomic, etc. | d4data/bias-detection-model (local) |
| **Political lean** | Left / Center / Right classification | matous-volf/political-leaning-politics (local) |
| **Bias evidence** | Sentence-level bias extraction with confidence scores | Same bias model, per-sentence |
| **Entity framing** | Maps named entities to their bias associations | GLiNER NER + bias cross-reference |
| **Bias index** | 0–100 composite score (type signal + political extremity + sentiment gap + entity framing + density) | Custom weighted formula |
| **Summarize** | 5-bullet key point summary | Groq API — llama-3.1-8b-instant |
| **Neutral rewrite** | Rewrites the top 3 most biased sentences in neutral language | Groq API — llama-3.1-8b-instant |
| **Compare** | Side-by-side bias analysis of two articles on the same topic | Full pipeline x2, delta computation |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Frontend — Next.js 14 / React 18 / Tailwind CSS    │
│  Editorial data-journalism aesthetic                 │
│  localhost:3000                                      │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (axios, FormData)
┌──────────────────────▼──────────────────────────────┐
│  Backend — FastAPI / Uvicorn                         │
│  localhost:8000                                      │
│                                                      │
│  Services (sequenced for 6 GB VRAM):                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Language  │→ │Translate │→ │Sentiment │           │
│  │ (lingua) │  │(NLLB-200)│  │(pipeline)│           │
│  └──────────┘  └──┬───────┘  └──────────┘           │
│                   │ unload                            │
│  ┌──────────┐  ┌──▼───────┐  ┌──────────┐           │
│  │  Bias    │→ │ Entities │→ │Bias Index│            │
│  │(d4data)  │  │ (GLiNER) │  │(compute) │           │
│  └──────────┘  └──────────┘  └──┬───────┘           │
│                                 │ unload all          │
│  ┌──────────┐  ┌──────────┐    │                     │
│  │ Summary  │← │ Rewrite  │← ──┘                    │
│  │(Groq API)│  │(Groq API)│                          │
│  └──────────┘  └──────────┘                          │
└──────────────────────────────────────────────────────┘
```

Models are loaded and unloaded in sequence to fit within 6 GB VRAM. HuggingFace transformers models run first, get fully unloaded (`del model + torch.cuda.empty_cache()`), then Groq API handles summarization and rewrites.

---

## Frontend Design

No glassmorphism. No gradients. Editorial data-journalism aesthetic inspired by Reuters Graphics, The Pudding, and NYT Interactive.

- **Background**: `#0d0d0d` (near-black)
- **Typography**: Syne (headings), DM Sans (body), DM Mono (data labels)
- **Accent**: `#d4372c` (ink-red)
- **Corners**: Sharp (0px border-radius)
- **Panels**: Bias gauge, evidence sentences, entity-bias graph, sentiment comparison, neutral rewrites

---

## Setup

### Prerequisites

- Python 3.12
- Node.js 18+
- NVIDIA GPU with 6+ GB VRAM (or CPU-only with longer inference times)
- Groq API key (free tier works)

### Backend

```bash
cd backend

# Install dependencies
py -3.12 -m pip install -r requirements.txt

# Upgrade transformers and gliner (required)
py -3.12 -m pip install transformers==5.3.0 gliner==0.2.25

# Start server
py -3.12 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## Usage

1. **URL tab** — paste a news article URL. Some sites (NDTV, paywalled outlets) block automated scraping; if you get a 422, switch to the Text tab.
2. **Text tab** — paste article text directly. Most reliable input method.
3. **PDF tab** — upload a PDF news article or report.
4. **Compare tab** — enter two article URLs to compare bias side-by-side.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analyze` | Analyze a single article (URL, text, or PDF) |
| `POST` | `/api/compare` | Compare two articles by URL |
| `GET`  | `/docs` | Interactive API docs (Swagger UI) |

---

## Key Technical Decisions

- **VRAM sequencing**: Models are loaded/unloaded in strict sequence rather than kept resident. This lets the full pipeline run on a 6 GB GPU.
- **Groq for generation**: Local Ollama models failed on the installed version (0.17.6). Groq's `llama-3.1-8b-instant` is used for summarization and neutral rewrites — fast, free tier, and reliable.
- **Composite bias index**: Weighted formula combining 5 signals (bias type confidence, political extremity, headline-body sentiment gap, entity framing ratio, biased sentence density) into a single 0–100 score.
- **Graceful degradation**: Every pipeline step has try/except. If GLiNER fails, entity mapping returns `[]`. If Groq fails, summaries return fallback text. The pipeline never crashes.

---

## Project Structure

```
Hack/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, routers
│   ├── requirements.txt
│   ├── models/
│   │   └── schemas.py           # Pydantic models
│   ├── routers/
│   │   ├── analyze.py           # POST /api/analyze
│   │   └── compare.py           # POST /api/compare
│   └── services/
│       ├── extractor.py         # URL/text extraction
│       ├── pdf_extractor.py     # PDF extraction
│       ├── language.py          # Language detection
│       ├── translator.py        # NLLB translation
│       ├── summarizer.py        # Groq summarization + rewrite
│       ├── sentiment.py         # Sentiment analysis
│       ├── bias.py              # Bias classification + evidence
│       └── entities.py          # GLiNER entity-bias mapping
├── frontend/
│   ├── package.json
│   ├── tailwind.config.ts
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── globals.css
│       │   └── page.tsx
│       ├── components/
│       │   ├── InputPanel.tsx
│       │   ├── BiasPanel.tsx
│       │   ├── EvidencePanel.tsx
│       │   ├── EntityGraph.tsx
│       │   ├── SummaryPanel.tsx
│       │   ├── SentimentPanel.tsx
│       │   ├── NeutralRewritePanel.tsx
│       │   └── CompareView.tsx
│       └── lib/
│           ├── types.ts
│           └── api.ts
└── README.md
```

---

## Team

**Lexo** — built at hackathon, March 2026.
