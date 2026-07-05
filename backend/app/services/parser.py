"""
Document text extraction service.
Handles PDF (via PyMuPDF) and DOCX (via python-docx) parsing.
"""
from pypdf import PdfReader
from docx import Document as DocxDocument
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    text_parts = []
    try:
        reader = PdfReader(BytesIO(file_bytes))
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    full_text = "\n\n".join(text_parts)
    if not full_text.strip():
        raise ValueError("The PDF appears to contain no extractable text. It may be a scanned/image-only PDF.")
    return full_text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file."""
    try:
        doc = DocxDocument(BytesIO(file_bytes))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")

    full_text = "\n\n".join(text_parts)
    if not full_text.strip():
        raise ValueError("The DOCX file appears to be empty or contains no extractable text.")
    return full_text


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from a file based on its extension.
    Returns the extracted text string.
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}. Only PDF and DOCX files are accepted.")
