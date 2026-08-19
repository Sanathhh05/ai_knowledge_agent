"""
Embedding service — generates vector embeddings using Ollama (local).

Default model: bge-m3 (1024 dimensions).
Talks to Ollama's /api/embed endpoint.
"""
from __future__ import annotations

import os
import logging
import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3:latest")

_TIMEOUT = 120.0  # seconds — first call may need to load the model


def generate_embedding(text: str) -> list[float]:
    """Generate a single embedding vector for the given text.

    Returns the embedding list, or raises on failure.
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text.")

    response = httpx.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": text},
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(f"Ollama embedding error: {data['error']}")

    return data["embeddings"][0]


def generate_embeddings(texts: list[str]) -> list[list[float] | None]:
    """Generate embeddings for a batch of texts.

    Returns a list the same length as `texts`. Each element is either
    the embedding vector or None if that particular text failed (e.g.
    degenerate input that produces NaN).
    """
    if not texts:
        return []

    results: list[list[float] | None] = []
    for text in texts:
        clean = text if text.strip() else " "
        try:
            response = httpx.post(
                f"{OLLAMA_BASE_URL}/api/embed",
                json={"model": EMBEDDING_MODEL, "input": clean},
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                logger.warning("Ollama returned error for chunk: %s", data["error"])
                results.append(None)
            else:
                results.append(data["embeddings"][0])
        except Exception as e:
            logger.warning("Failed to embed chunk (len=%d): %s", len(clean), e)
            results.append(None)

    return results
