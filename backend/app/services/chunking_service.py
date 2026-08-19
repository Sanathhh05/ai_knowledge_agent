"""
Chunking service for AI Knowledge Assistant.

Implements a recursive character text splitter (inspired by the reference
project's use of LangChain RecursiveCharacterTextSplitter) without the
LangChain dependency.

Strategy:
  - Target chunk size: ~3500 characters (~800-1000 tokens)
  - Overlap: ~500 characters (~100-150 tokens)
  - Split hierarchy: paragraphs (\\n\\n) > lines (\\n) > sentences (. ) > spaces
  - Each chunk gets a sequential chunk_index starting at 0
"""

from __future__ import annotations

import re


# Approximate 800-1000 tokens at ~4 chars/token
CHUNK_SIZE = 3500
CHUNK_OVERLAP = 500
SEPARATORS = ["\n\n", "\n", ". ", " "]


def _split_text_recursive(
    text: str,
    separators: list[str],
    chunk_size: int,
) -> list[str]:
    """Recursively split text using a hierarchy of separators."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    # Find the best separator that exists in the text
    separator = ""
    for sep in separators:
        if sep in text:
            separator = sep
            break

    if not separator:
        # No separator found -- hard split by chunk_size
        chunks = []
        for i in range(0, len(text), chunk_size):
            piece = text[i : i + chunk_size]
            if piece.strip():
                chunks.append(piece)
        return chunks

    # Split on the chosen separator
    parts = text.split(separator)
    remaining_separators = separators[separators.index(separator) + 1 :]

    result: list[str] = []
    current = ""

    for part in parts:
        candidate = (current + separator + part) if current else part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current.strip():
                result.append(current)
            # If the part itself is too large, recurse with next separators
            if len(part) > chunk_size and remaining_separators:
                sub_chunks = _split_text_recursive(
                    part, remaining_separators, chunk_size
                )
                result.extend(sub_chunks)
                current = ""
            else:
                current = part

    if current.strip():
        result.append(current)

    return result


def _add_overlap(chunks: list[str], overlap: int) -> list[str]:
    """Add overlap from the end of the previous chunk to the start of each chunk."""
    if not chunks or overlap <= 0:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-overlap:]
        # Only add overlap if it doesn't duplicate the start
        if not chunks[i].startswith(prev_tail):
            result.append(prev_tail + chunks[i])
        else:
            result.append(chunks[i])
    return result


def normalize_text(text: str) -> str:
    """
    Normalize text before chunking:
    - Strip leading/trailing whitespace
    - Collapse runs of 3+ newlines to 2
    - Collapse multiple spaces to single space (per line)
    - Preserve paragraph structure
    """
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces (but not newlines)
    text = re.sub(r"[^\S\n]+", " ", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    """
    Split text into overlapping chunks.

    Returns:
        List of dicts with keys: content, chunk_index
    """
    normalized = normalize_text(text)
    if not normalized:
        return []

    raw_chunks = _split_text_recursive(normalized, SEPARATORS, chunk_size)
    overlapped = _add_overlap(raw_chunks, chunk_overlap)

    return [
        {"content": chunk.strip(), "chunk_index": i}
        for i, chunk in enumerate(overlapped)
        if chunk.strip()
    ]
