import fitz  # PyMuPDF
import pdfplumber
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


def extract_from_pdf(file_bytes: bytes, filename: str = "upload.pdf") -> dict:
    """Extract text from PDF using PyMuPDF with pdfplumber fallback."""
    result = {"title": filename, "text": "", "author": "", "date": "", "source": "pdf_upload"}

    # Primary: PyMuPDF
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()

        text = "\n".join(text_parts).strip()
        if len(text) > 100:
            result["text"] = text
            result["title"] = _extract_pdf_title(text, filename)
            return result
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed: {e}")

    # Fallback: pdfplumber (better for tables)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        with pdfplumber.open(tmp_path) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        text = "\n".join(text_parts).strip()
        if len(text) > 50:
            result["text"] = text
            result["title"] = _extract_pdf_title(text, filename)
            return result
    except Exception as e:
        logger.error(f"pdfplumber fallback also failed: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    raise ValueError("Could not extract text from PDF")


def _extract_pdf_title(text: str, fallback: str) -> str:
    """Try to extract a title from the first line of PDF text."""
    lines = text.strip().split("\n")
    for line in lines[:5]:
        cleaned = line.strip()
        if 10 < len(cleaned) < 200:
            return cleaned
    return fallback
