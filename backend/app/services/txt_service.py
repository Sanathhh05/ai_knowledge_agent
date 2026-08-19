"""
TXT text extraction service.

Reads plain text files with UTF-8 encoding.
Handles BOM markers and validates content.
"""

from __future__ import annotations


def extract_text_from_txt(file_bytes: bytes) -> dict:
    """
    Extract text from a TXT file.

    Args:
        file_bytes: Raw text file content.

    Returns:
        dict with keys:
          - text: the file content as a string

    Raises:
        ValueError: If the file is empty or cannot be decoded.
    """
    # Try UTF-8 first (with BOM handling), then latin-1 as fallback
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("latin-1")
        except UnicodeDecodeError:
            raise ValueError("File could not be decoded. Ensure it is a valid text file.")

    if not text.strip():
        raise ValueError("Text file is empty.")

    return {"text": text}
