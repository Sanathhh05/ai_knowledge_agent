"""
SQLAlchemy database setup for AI Knowledge Assistant.

Provides:
- engine: SQLAlchemy async-compatible engine bound to DATABASE_URL
- SessionLocal: session factory for creating database sessions
- Base: declarative base for all ORM models
- get_db: FastAPI dependency that yields a database session
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # verify connection is alive before each use
    pool_size=5,
    max_overflow=10,
    echo=False,           # set True during local debugging to log SQL
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy models."""
    pass


def get_db():
    """
    FastAPI dependency that yields a database session.

    Usage:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_connection() -> None:
    """Verify the database is reachable. Raises on failure."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
