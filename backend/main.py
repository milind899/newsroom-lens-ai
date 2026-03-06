import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="AI News Analyzer - Multilingual Bias Detection",
    description="Analyze news articles for bias, sentiment, and generate neutral summaries",
    version="1.0.0",
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from routers.analyze import router as analyze_router
from routers.compare import router as compare_router
from routers.report import router as report_router

app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
app.include_router(compare_router, prefix="/api", tags=["Comparison"])
app.include_router(report_router, prefix="/api", tags=["Reports"])


@app.get("/")
async def root():
    return {
        "name": "AI News Analyzer",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "compare": "POST /api/compare",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
