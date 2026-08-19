"""
LLM service — generates text answers using Ollama (local).

Default model: qwen3:8b.
Talks to Ollama's /api/generate endpoint.
"""
from __future__ import annotations

import os
import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3:8b")

_TIMEOUT = 180.0  # LLM generation can be slow on modest hardware


def generate_answer(query: str, context_chunks: list[dict], chat_history: list[dict] = None) -> str:
    """Given a user query, retrieved context chunks, and optional chat history, generate a RAG answer.

    Each context chunk is expected to have at least 'content' and 'source_name'.
    Each chat_history dict should have 'role' (user/assistant) and 'content'.
    """
    # Build context block with source attribution
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        source = chunk.get("source_name", "unknown")
        content = chunk.get("content", "")
        context_parts.append(f"[Source {i}: {source}]\n{content}")

    context_block = "\n\n".join(context_parts) if context_parts else "No source context provided."

    # Build chat history block
    history_block = ""
    if chat_history:
        history_parts = []
        for msg in chat_history:
            role_name = "User" if msg["role"] == "user" else "Assistant"
            history_parts.append(f"{role_name}: {msg['content']}")
        history_block = "\nCONVERSATION HISTORY:\n" + "\n".join(history_parts) + "\n"

    prompt = f"""/no_think
You are an AI Knowledge Assistant. Answer the user's current question using ONLY the provided SOURCE CONTEXT.

Do not invent facts that are not supported by the context.
If the answer cannot be determined from the provided sources, clearly state: "I couldn't find information about that in your uploaded sources."
When multiple sources provide relevant information, synthesize them.
Do not mention internal retrieval mechanics.
Prefer precise answers. Cite the source name in brackets (e.g., [Source Name]) when referencing information.
{history_block}
SOURCE CONTEXT:
{context_block}

CURRENT QUESTION:
{query}

Answer:"""

    response = httpx.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 1024,
            },
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()
