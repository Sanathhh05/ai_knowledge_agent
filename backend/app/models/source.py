"""
Source ORM model.

Table: sources
- id            UUID primary key
- user_id       FK to users.id (every source belongs to one user)
- name          display name (e.g. filename, video title)
- source_type   enum: pdf, docx, txt, youtube, web
- url           nullable (present for youtube/web, absent for uploads)
- status        enum: processing, completed, failed
- error_message nullable (populated on failure)
- created_at    timestamp with timezone
- updated_at    timestamp with timezone
"""

import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="processing",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    chunks = relationship(
        "SourceChunk",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Source id={self.id} name={self.name!r} type={self.source_type}>"
