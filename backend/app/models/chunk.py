"""
SourceChunk ORM model.

Table: source_chunks
- id           UUID primary key
- source_id    FK to sources.id
- user_id      FK to users.id (denormalized for efficient user-scoped queries)
- content      the chunk text
- chunk_index  ordered position within the source (0-based)
- metadata     JSONB for source-type-specific info (page, timestamps, etc.)
- created_at   timestamp with timezone
"""

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SourceChunk(Base):
    __tablename__ = "source_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
    )
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    embedding = mapped_column(
        Vector(1024),
        nullable=True,
    )

    # Relationships
    source = relationship("Source", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<SourceChunk id={self.id} source={self.source_id} index={self.chunk_index}>"
