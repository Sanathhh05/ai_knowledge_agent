"""
PDF text extraction service.

Uses PyMuPDF (fitz) for reliable, page-by-page text extraction.
Preserves page number metadata for each page's text.
"""

from __future__ import annotations

import pymupdf  # PyMuPDF


def extract_text_from_pdf(file_bytes: bytes) -> dict:
    """
    Extract text from a PDF file.

    Args:
        file_bytes: Raw PDF file content.

    Returns:
        dict with keys:
          - text: concatenated full text
          - pages: list of { page_number, text } dicts

    Raises:
        ValueError: If the PDF contains no extractable text.
    """
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    pages: list[dict] = []
    full_text_parts: list[str] = []

    try:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            if page_text and page_text.strip():
                pages.append({
                    "page_number": page_num + 1,  # 1-based
                    "text": page_text.strip(),
                })
                full_text_parts.append(page_text.strip())
    finally:
        doc.close()

    full_text = "\n\n".join(full_text_parts)

    if not full_text.strip():
        raise ValueError(
            "PDF contains no extractable text. "
            "It may be image-based (OCR is not supported in this phase)."
        )

    return {
        "text": full_text,
        "pages": pages,
    }
