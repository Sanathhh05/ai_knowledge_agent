"""
Ingestion orchestrator service.

Central pipeline that coordinates:
  Source record creation -> Text extraction -> Normalization -> Chunking -> Storage

All source types flow through this single pipeline. The source-specific
extractors are called based on source_type, then the common chunking
service processes the text into chunks stored in PostgreSQL.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.chunk import SourceChunk
from app.models.source import Source
from app.services.chunking_service import chunk_text
from app.services.docx_service import extract_text_from_docx
from app.services.pdf_service import extract_text_from_pdf
from app.services.txt_service import extract_text_from_txt
from app.services.web_service import extract_text_from_url
from app.services.youtube_service import fetch_transcript
from app.services.embedding_service import generate_embeddings


def _store_chunks(
    db: Session,
    source: Source,
    chunks: list[dict],
    base_metadata: dict[str, Any] | None = None,
) -> int:
    """Store chunked text in the source_chunks table. Returns chunk count."""
    # Generate embeddings for the batch
    texts = [chunk_data["content"] for chunk_data in chunks]
    embeddings = generate_embeddings(texts)
    
    for chunk_data, embedding in zip(chunks, embeddings):
        meta = dict(base_metadata) if base_metadata else {}
        meta["chunk_index"] = chunk_data["chunk_index"]

        db_chunk = SourceChunk(
            source_id=source.id,
            user_id=source.user_id,
            content=chunk_data["content"],
            chunk_index=chunk_data["chunk_index"],
            metadata_=meta,
            embedding=embedding,
        )
        db.add(db_chunk)

    return len(chunks)


def ingest_file(
    db: Session,
    user_id: uuid.UUID,
    filename: str,
    file_bytes: bytes,
    source_type: str,
) -> Source:
    """
    Ingest an uploaded file (PDF, DOCX, or TXT).

    Creates the source record, extracts text, chunks it, stores chunks,
    and updates the source status.
    """
    # 1. Create source record with status=processing
    source = Source(
        user_id=user_id,
        name=filename,
        source_type=source_type,
        status="processing",
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        # 2. Extract text based on source type
        if source_type == "pdf":
            result = extract_text_from_pdf(file_bytes)
            base_metadata = {"source_type": "pdf"}
        elif source_type == "docx":
            result = extract_text_from_docx(file_bytes)
            base_metadata = {"source_type": "docx"}
        elif source_type == "txt":
            result = extract_text_from_txt(file_bytes)
            base_metadata = {"source_type": "txt"}
        else:
            raise ValueError(f"Unsupported file type: {source_type}")

        # 3. Chunk the text
        chunks = chunk_text(result["text"])
        if not chunks:
            raise ValueError("No text content could be extracted from the file.")

        # 4. Store chunks
        _store_chunks(db, source, chunks, base_metadata)

        # 5. Mark completed
        source.status = "completed"
        db.commit()
        db.refresh(source)

    except Exception as e:
        source.status = "failed"
        source.error_message = str(e)
        db.commit()
        db.refresh(source)

    return source


def ingest_youtube(
    db: Session,
    user_id: uuid.UUID,
    url: str,
) -> Source:
    """
    Ingest a YouTube video by fetching its transcript.

    Creates the source record, fetches transcript, chunks it, stores chunks.
    """
    source = Source(
        user_id=user_id,
        name=url,  # Will be updated with video title
        source_type="youtube",
        url=url,
        status="processing",
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        # Fetch transcript
        result = fetch_transcript(url)

        # Update source name with video title
        source.name = result.get("title", url)

        # Chunk the transcript text
        chunks = chunk_text(result["text"])
        if not chunks:
            raise ValueError("Transcript is too short to process.")

        # Build metadata with video info
        base_metadata = {
            "source_type": "youtube",
            "video_id": result.get("video_id", ""),
            "url": url,
        }

        _store_chunks(db, source, chunks, base_metadata)

        source.status = "completed"
        db.commit()
        db.refresh(source)

    except Exception as e:
        source.status = "failed"
        source.error_message = str(e)
        db.commit()
        db.refresh(source)

    return source


def ingest_web_url(
    db: Session,
    user_id: uuid.UUID,
    url: str,
) -> Source:
    """
    Ingest a web page by fetching and extracting its text content.
    """
    source = Source(
        user_id=user_id,
        name=str(url),  # Will be updated with page title
        source_type="web",
        url=str(url),
        status="processing",
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        result = extract_text_from_url(str(url))

        # Update source name with page title
        source.name = result.get("title", str(url))

        chunks = chunk_text(result["text"])
        if not chunks:
            raise ValueError("No text content could be extracted from the page.")

        base_metadata = {
            "source_type": "web",
            "url": str(url),
        }

        _store_chunks(db, source, chunks, base_metadata)

        source.status = "completed"
        db.commit()
        db.refresh(source)

    except Exception as e:
        source.status = "failed"
        source.error_message = str(e)
        db.commit()
        db.refresh(source)

    return source
