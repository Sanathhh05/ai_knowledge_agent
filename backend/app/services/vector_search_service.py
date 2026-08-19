"""
Vector search service for retrieving relevant chunks from PostgreSQL + pgvector.
Uses cosine distance for similarity ranking.
"""
from __future__ import annotations

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.chunk import SourceChunk
from app.models.source import Source
from app.services.embedding_service import generate_embedding


def search_similar_chunks(
    db: Session,
    query: str,
    user_id: uuid.UUID,
    top_k: int = 5,
) -> list[dict]:
    """
    Search for the top-k most semantically similar chunks for a given user.
    Results are ordered by cosine similarity (highest first).
    """
    if top_k <= 0 or top_k > 50:
        top_k = 5

    # 1. Generate embedding for the query
    query_embedding = generate_embedding(query)

    # 2. Build query with explicit distance column
    distance_col = SourceChunk.embedding.cosine_distance(query_embedding).label("distance")

    stmt = (
        select(SourceChunk, Source, distance_col)
        .join(Source, SourceChunk.source_id == Source.id)
        .where(SourceChunk.user_id == user_id)
        .where(SourceChunk.embedding.is_not(None))
        .order_by(distance_col)
        .limit(top_k)
    )

    results = db.execute(stmt).all()

    # 3. Format results
    formatted = []
    for chunk, source, distance in results:
        similarity = 1.0 - float(distance)
        formatted.append({
            "chunk_id": str(chunk.id),
            "source_id": str(source.id),
            "source_name": source.name,
            "content": chunk.content,
            "metadata": chunk.metadata_,
            "score": round(similarity, 4),
        })

    return formatted
