"""
DOCX text extraction service.

Uses python-docx to extract paragraphs from .docx files.
Preserves paragraph index metadata.
"""

from __future__ import annotations

import io

from docx import Document


def extract_text_from_docx(file_bytes: bytes) -> dict:
    """
    Extract text from a DOCX file.

    Args:
        file_bytes: Raw DOCX file content.

    Returns:
        dict with keys:
          - text: concatenated full text
          - paragraphs: list of { paragraph_index, text } dicts

    Raises:
        ValueError: If the DOCX contains no readable text.
    """
    doc = Document(io.BytesIO(file_bytes))
    paragraphs: list[dict] = []
    full_text_parts: list[str] = []

    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            paragraphs.append({
                "paragraph_index": i,
                "text": text,
            })
            full_text_parts.append(text)

    full_text = "\n\n".join(full_text_parts)

    if not full_text.strip():
        raise ValueError("DOCX contains no readable text.")

    return {
        "text": full_text,
        "paragraphs": paragraphs,
    }
