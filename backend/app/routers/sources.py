"""
Sources router.

Endpoints:
  POST   /sources/upload        -- upload a PDF, DOCX, or TXT file
  POST   /sources/youtube       -- add a YouTube video by URL
  POST   /sources/url           -- add a web page by URL
  GET    /sources               -- list current user's sources
  GET    /sources/{source_id}   -- get source detail with chunks
  DELETE /sources/{source_id}   -- delete a source and its chunks

All endpoints require JWT authentication. Sources are scoped to the
authenticated user -- a user can never access another user's sources.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chunk import SourceChunk
from app.models.source import Source
from app.models.user import User
from app.schemas.source import (
    SourceChunkResponse,
    SourceDetailResponse,
    SourceResponse,
    WebURLRequest,
    YouTubeRequest,
    SearchRequest,
    SearchResponse,
    AskRequest,
    AskResponse,
)
from app.services.ingestion_service import ingest_file, ingest_web_url, ingest_youtube
from app.services.vector_search_service import search_similar_chunks
from app.services.embedding_service import generate_embeddings
from app.services.llm_service import generate_answer
from app.utils.security import get_current_user

router = APIRouter(tags=["Sources"])

# Allowed upload extensions and max file size (10 MB)
_ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _get_extension(filename: str) -> str:
    """Extract lowercase file extension without the dot."""
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def _build_source_response(source: Source, db: Session) -> SourceResponse:
    """Build a SourceResponse with chunk_count from the database."""
    chunk_count = (
        db.query(func.count(SourceChunk.id))
        .filter(SourceChunk.source_id == source.id)
        .scalar()
    )
    return SourceResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type,
        status=source.status,
        url=source.url,
        error_message=source.error_message,
        created_at=source.created_at,
        updated_at=source.updated_at,
        chunk_count=chunk_count or 0,
    )


# ---------------------------------------------------------------------------
# POST /sources/upload
# ---------------------------------------------------------------------------


@router.post(
    "/upload",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF, DOCX, or TXT file",
)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SourceResponse:
    """
    Upload and ingest a file.

    Supported formats: .pdf, .docx, .txt
    Maximum file size: 10 MB
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    ext = _get_extension(file.filename)
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(f'.{e}' for e in sorted(_ALLOWED_EXTENSIONS))}",
        )

    # Read file content
    file_bytes = await file.read()

    if len(file_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the {_MAX_FILE_SIZE // (1024*1024)} MB limit.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    source = ingest_file(
        db=db,
        user_id=current_user.id,
        filename=file.filename,
        file_bytes=file_bytes,
        source_type=ext,
    )

    return _build_source_response(source, db)


# ---------------------------------------------------------------------------
# POST /sources/youtube
# ---------------------------------------------------------------------------


@router.post(
    "/youtube",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a YouTube video by URL",
)
def add_youtube(
    payload: YouTubeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SourceResponse:
    """
    Fetch the transcript of a YouTube video, chunk it, and store it.

    The video must have captions available (manual or auto-generated).
    """
    source = ingest_youtube(
        db=db,
        user_id=current_user.id,
        url=payload.url,
    )

    return _build_source_response(source, db)


# ---------------------------------------------------------------------------
# POST /sources/url
# ---------------------------------------------------------------------------


@router.post(
    "/url",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a web page by URL",
)
def add_web_url(
    payload: WebURLRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SourceResponse:
    """
    Fetch a web page, extract readable text, chunk it, and store it.
    """
    source = ingest_web_url(
        db=db,
        user_id=current_user.id,
        url=str(payload.url),
    )

    return _build_source_response(source, db)


# ---------------------------------------------------------------------------
# GET /sources
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[SourceResponse],
    summary="List current user's sources",
)
def list_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SourceResponse]:
    """
    Return all sources belonging to the authenticated user.

    Sources from other users are never returned.
    """
    sources = (
        db.query(Source)
        .filter(Source.user_id == current_user.id)
        .order_by(Source.created_at.desc())
        .all()
    )

    return [_build_source_response(s, db) for s in sources]


# ---------------------------------------------------------------------------
# GET /sources/{source_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{source_id}",
    response_model=SourceDetailResponse,
    summary="Get source details with chunks",
)
def get_source(
    source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SourceDetailResponse:
    """
    Return a source and its chunks.

    Returns 404 if the source doesn't exist or belongs to another user
    (does not leak ownership information).
    """
    source = (
        db.query(Source)
        .filter(Source.id == source_id, Source.user_id == current_user.id)
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found.",
        )

    chunks = (
        db.query(SourceChunk)
        .filter(SourceChunk.source_id == source.id)
        .order_by(SourceChunk.chunk_index)
        .all()
    )

    chunk_responses = [
        SourceChunkResponse(
            id=c.id,
            chunk_index=c.chunk_index,
            content=c.content,
            metadata=c.metadata_,
        )
        for c in chunks
    ]

    return SourceDetailResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type,
        status=source.status,
        url=source.url,
        error_message=source.error_message,
        created_at=source.created_at,
        updated_at=source.updated_at,
        chunks=chunk_responses,
    )


# ---------------------------------------------------------------------------
# DELETE /sources/{source_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a source and its chunks",
)
def delete_source(
    source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a source and all its associated chunks (via cascade).

    Returns 404 if the source doesn't exist or belongs to another user.
    """
    source = (
        db.query(Source)
        .filter(Source.id == source_id, Source.user_id == current_user.id)
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found.",
        )

    db.delete(source)
    db.commit()


# ---------------------------------------------------------------------------
# POST /sources/embed-pending
# ---------------------------------------------------------------------------


@router.post(
    "/embed-pending",
    status_code=status.HTTP_200_OK,
    summary="Generate embeddings for existing chunks without them",
)
def embed_pending(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Finds chunks belonging to the current user that do not have an embedding,
    generates embeddings for them, and updates the database.
    This is useful for chunks that were generated in Phase 2 before embeddings were added.
    """
    pending_chunks = (
        db.query(SourceChunk)
        .filter(SourceChunk.user_id == current_user.id)
        .filter(SourceChunk.embedding.is_(None))
        .all()
    )

    if not pending_chunks:
        return {"message": "No pending chunks found for embedding.", "processed_count": 0}

    # Process in batches of 50
    batch_size = 50
    processed_count = 0
    skipped_count = 0

    for i in range(0, len(pending_chunks), batch_size):
        batch = pending_chunks[i : i + batch_size]
        texts = [chunk.content for chunk in batch]
        try:
            embeddings = generate_embeddings(texts)
            for chunk, embedding in zip(batch, embeddings):
                if embedding is not None:
                    chunk.embedding = embedding
                    processed_count += 1
                else:
                    skipped_count += 1
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate embeddings at batch {i//batch_size}. Error: {str(e)}",
            )

    return {
        "message": "Embedding generation complete.",
        "processed_count": processed_count,
        "skipped_count": skipped_count,
    }


# ---------------------------------------------------------------------------
# POST /sources/search
# ---------------------------------------------------------------------------


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search across sources using semantic retrieval",
)
def search_sources(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """
    Search across the user's sources using vector embeddings.
    Returns the top-K relevant chunks.
    """
    try:
        results = search_similar_chunks(
            db=db,
            query=payload.query,
            user_id=current_user.id,
            top_k=payload.top_k,
        )
        return SearchResponse(query=payload.query, results=results)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform semantic search: {str(e)}",
        )


# ---------------------------------------------------------------------------
# POST /sources/ask  (RAG test endpoint)
# ---------------------------------------------------------------------------


@router.post(
    "/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question using RAG (retrieve + generate)",
)
def ask_question(
    payload: AskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AskResponse:
    """
    Retrieve relevant chunks via semantic search, then generate an
    LLM answer using the retrieved context.
    """
    try:
        # 1. Retrieve relevant chunks
        results = search_similar_chunks(
            db=db,
            query=payload.query,
            user_id=current_user.id,
            top_k=payload.top_k,
        )

        if not results:
            return AskResponse(
                query=payload.query,
                answer="No relevant sources found. Please upload some documents first.",
                sources=[],
            )

        # 2. Generate answer using LLM
        answer = generate_answer(query=payload.query, context_chunks=results)

        return AskResponse(
            query=payload.query,
            answer=answer,
            sources=results,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}",
        )
