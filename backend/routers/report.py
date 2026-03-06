"""Router for PDF report generation."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import logging

from services.report import generate_pdf_report

logger = logging.getLogger(__name__)
router = APIRouter()


class ReportRequest(BaseModel):
    """Accepts the full analysis result JSON to convert to PDF."""
    title: str
    source_url: Optional[str] = None
    original_text: Optional[str] = None
    translated_text: Optional[str] = None
    language: Optional[dict] = None
    summary: Optional[list] = None
    sentiment: Optional[dict] = None
    bias: Optional[dict] = None
    neutral_rewrites: Optional[list] = None
    source_credibility: Optional[dict] = None
    claims: Optional[list] = None


@router.post("/report/pdf")
async def generate_report(data: ReportRequest):
    """Generate a PDF report from analysis results."""
    try:
        pdf_bytes = generate_pdf_report(data.model_dump())
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="newsroom-lens-report.pdf"',
            },
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
