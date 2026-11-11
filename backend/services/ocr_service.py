"""
services/ocr_service.py
------------------------
Extracts text from PDF documents using PyMuPDF (fitz).

PyMuPDF reads the embedded text layer directly, which covers the vast
majority of "digital" PDFs (contracts, newsletters, reports, etc.). For
scanned/image-only pages (no text layer), we fall back to rendering the
page to an image and running Tesseract OCR over it, so the pipeline still
produces usable text for scanned documents.
"""

import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Minimum characters of native text before we consider a page "scanned"
# and worth OCR-ing instead.
_MIN_TEXT_LEN_PER_PAGE = 20


def _ocr_page_image(page: "fitz.Page") -> str:
    """Render a page to a high-res image and OCR it with pytesseract.

    Imported lazily so the app still runs (falling back to native text
    only) in environments where the Tesseract binary isn't installed.
    """
    try:
        import io

        import pytesseract
        from PIL import Image

        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img)
    except Exception as exc:  # pragma: no cover - OCR is best-effort
        logger.warning("OCR fallback unavailable/failed for a page: %s", exc)
        return ""


def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extract text from every page of a PDF.

    Returns:
        {
          "page_count": int,
          "pages": [ {"page_number": 1, "text": "..."}, ... ],
          "full_text": "concatenated text across all pages",
        }
    """
    pages = []
    doc = fitz.open(file_path)
    try:
        for index, page in enumerate(doc):
            text = page.get_text("text").strip()

            if len(text) < _MIN_TEXT_LEN_PER_PAGE:
                # Likely a scanned/image page - try OCR as a fallback.
                ocr_text = _ocr_page_image(page).strip()
                if len(ocr_text) > len(text):
                    text = ocr_text

            pages.append({"page_number": index + 1, "text": text})

        page_count = doc.page_count
    finally:
        doc.close()

    full_text = "\n\n".join(p["text"] for p in pages if p["text"])

    return {
        "page_count": page_count,
        "pages": pages,
        "full_text": full_text,
    }


def chunk_text(full_text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """
    Split extracted text into overlapping chunks suitable for embedding.
    Overlap preserves context across chunk boundaries so semantic search
    doesn't miss information that straddles two chunks.
    """
    words = full_text.split()
    if not words:
        return []

    chunks = []
    step = max(chunk_size - overlap, 1)
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break
    return chunks
