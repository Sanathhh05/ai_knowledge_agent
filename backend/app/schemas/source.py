"""
Pydantic schemas for source endpoints.

Request/response models for file upload, YouTube, web URL ingestion,
and source listing.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, HttpUrl, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class YouTubeRequest(BaseModel):
    """Request body for POST /sources/youtube."""
    url: str

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        v = v.strip()
        if not any(domain in v for domain in [
            "youtube.com", "youtu.be", "youtube-nocookie.com"
        ]):
            raise ValueError("URL must be a valid YouTube URL.")
        return v


class WebURLRequest(BaseModel):
    """Request body for POST /sources/url."""
    url: HttpUrl

class SearchRequest(BaseModel):
    """Request body for POST /sources/search."""
    query: str
    top_k: int = 5

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        if v < 1 or v > 50:
            raise ValueError("top_k must be between 1 and 50.")
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SourceChunkResponse(BaseModel):
    """A single chunk from a source."""
    id: uuid.UUID
    chunk_index: int
    content: str
    metadata: dict[str, Any] | None = None

    model_config = {"from_attributes": True}

    @field_validator("metadata", mode="before")
    @classmethod
    def read_metadata_column(cls, v: Any) -> Any:
        """Handle the mapped column name `metadata_` -> `metadata`."""
        return v


class SourceResponse(BaseModel):
    """Source summary returned in list endpoints."""
    id: uuid.UUID
    name: str
    source_type: str
    status: str
    url: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    chunk_count: int = 0

    model_config = {"from_attributes": True}


class SourceDetailResponse(BaseModel):
    """Source with its chunks, returned by GET /sources/{id}."""
    id: uuid.UUID
    name: str
    source_type: str
    status: str
    url: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    chunks: list[SourceChunkResponse] = []

    model_config = {"from_attributes": True}


class SearchResultResponse(BaseModel):
    """Single result item from a search query."""
    chunk_id: str
    source_id: str
    source_name: str
    content: str
    metadata: dict[str, Any] | None = None
    score: float

class SearchResponse(BaseModel):
    """Response body for POST /sources/search."""
    query: str
    results: list[SearchResultResponse]


class AskRequest(BaseModel):
    """Request body for POST /sources/ask."""
    query: str
    top_k: int = 5

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        if v < 1 or v > 50:
            raise ValueError("top_k must be between 1 and 50.")
        return v


class AskResponse(BaseModel):
    """Response body for POST /sources/ask."""
    query: str
    answer: str
    sources: list[SearchResultResponse]
