# Newsroom Lens: Advanced Media Bias Analytical Pipeline

Newsroom Lens is a high-fidelity media intelligence platform engineered to identify linguistic bias, political inclination, and sentiment manipulation in modern news reporting. By processing URLs, raw text, or digital documents, the system executes a multi-stage analytical pipeline to quantify editorial slant and surface hidden framing.

The architecture is optimized for efficient inference on consumer-grade hardware, utilizing a hybrid model of local transformer execution and cloud-based large language model (LLM) processing.

---

## Analytical Pipeline

| Pipeline Stage | Functionality | Technology Stack |
|----------------|---------------|------------------|
| **Extraction**  | Article retrieval from URLs, text, or PDFs | Trafilatura, Readability-lxml, PyMuPDF |
| **Language**    | Automatic detection of 38+ languages | Lingua Language Detector |
| **Translation** | Bidirectional translation for non-English sources | Google Gemini 1.5 Flash API |
| **Sentiment**   | Comparison of headline vs. body sentiment | DeBERTa Multilingual Sentiment (Local) |
| **Bias Analysis**| Categorization of bias types (Political, Nationalistic, etc.) | ModernBERT Bias Classifier (Local) |
| **Political Lean**| Context-aware political leaning detection | Groq API - Llama 3.1 8B |
| **Entity Mapping**| Scoring bias associated with specific entities | GLiNER NER + Custom Cross-Reference |
| **Bias Index**  | 0-100 score based on weighted metrics | Custom Analytical Formula |
| **Fact Checking**| Extraction and verification of core factual claims | Groq API |
| **Neutrality**  | Automated generation of neutral summaries and rewrites | Groq API |

---

## Infrastructure and Design

The application follows a decoupled architecture designed for efficiency and speed:

- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS. The interface utilizes a high-contrast editorial aesthetic inspired by modern data journalism.
- **Backend**: FastAPI with Uvicorn, implementing a sequenced pipeline to manage VRAM usage.
- **Inference Strategy**: Local Transformer models are utilized for fast, privacy-focused classification, while high-latency reasoning tasks are offloaded to Groq and Gemini APIs.

### Interface Specifications
- **Typography**: Syne (Headings), DM Sans (Body), DM Mono (Technical labels).
- **Core Aesthetic**: Dark mode interface (#0D0D0D) with high-visibility accents (#D4372C).
- **Deployment**: Integrated start script for simultaneous backend and frontend execution.

---

## Installation and Setup

### Prerequisites
- Python 3.12
- Node.js 18 or higher
- NVIDIA GPU with 6GB+ VRAM (Recommended for local model performance)
- Valid API Keys for Groq and Google Gemini

### Configuration
1. Navigate to the `backend` directory.
2. Create a `.env` file with the following environment variables:
   ```env
   GROQ_API_KEY=your_groq_key_here
   GEMINI_API_KEY=your_gemini_key_here
   ```

### Execution
Use the provided `start.bat` file in the root directory to launch both services automatically:
```bash
./start.bat
```

Alternatively, launch manually:

**Backend Service:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend Service:**
```bash
cd frontend
npm install
npm run dev
```

The application will be accessible at **http://localhost:3000**.

---

## Usage Patterns

- **URL Analysis**: Analyze live news articles directly via their web address. Note that some domains with aggressive anti-scraping measures may require the use of the Text tab.
- **Direct Text**: Paste article content for the most consistent analysis results.
- **PDF Extraction**: Process digital documents or archived news reports.
- **Comparative Analysis**: Input two URLs covering the same event to contrast editorial differences and framing side-by-side.
- **Export**: Generate comprehensive PDF reports of the analysis for local archiving.

---

## System Architecture Details

The backend implements strict model sequencing. Local models (Sentiment, Bias, NER) are loaded into VRAM only when needed and forcefully unloaded thereafter to maintain a low hardware footprint. High-level summarization and rewrite tasks are performed via API to ensure rapid response times and global political context awareness.

### Project Structure
```
Hack/
├── backend/
│   ├── main.py                  # API definitions and middleware
│   ├── .env                     # Private configuration (Excluded from Git)
│   ├── routers/                 # API endpoint handlers
│   └── services/                # Core AI and data processing logic
├── frontend/
│   ├── src/app/                 # Next.js pages and styles
│   ├── src/components/          # Modular UI components
│   └── src/lib/                 # API client and type definitions
├── start.bat                    # Integrated launch script
└── README.md                    # System documentation
```
