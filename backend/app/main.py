"""
FastAPI application entry point for AI Knowledge Assistant.

Responsibilities:
- Create and configure the FastAPI app
- Configure CORS (allow only FRONTEND_URL)
- Configure Swagger JWT security scheme
- Register routers
- Create database tables on startup
- Expose health check endpoint
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.database import Base, engine, verify_connection
from app.routers import auth as auth_router
from app.routers import sources as sources_router
from app.routers import conversations as conversations_router

load_dotenv()

FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://ai-knowledge-agent-rouge.vercel.app")

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Knowledge Assistant API",
    description=(
        "Backend API for the AI Knowledge Assistant. "
        "Handles authentication, source ingestion, RAG, chat, and voice."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router.router, prefix="/auth")
app.include_router(sources_router.router, prefix="/sources")
app.include_router(conversations_router.router, prefix="/conversations")

# ---------------------------------------------------------------------------
# Startup: create tables & verify DB connection
# ---------------------------------------------------------------------------


@app.on_event("startup")
def on_startup() -> None:
    """
    Run on application startup:
    1. Verify the database is reachable.
    2. Create all tables that don't yet exist (SQLAlchemy metadata).
       Tables already present are left untouched.
    """
    verify_connection()
    # Import models so their metadata is registered with Base before create_all
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/", tags=["Health"], summary="Health check")
def health_check() -> dict:
    """Returns a simple status response to confirm the API is running."""
    return {"status": "ok", "service": "AI Knowledge Assistant API", "version": "0.1.0"}


@app.get("/health", tags=["Health"], summary="Health check (alias)")
def health() -> dict:
    """Alias for the root health check."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Custom OpenAPI schema — adds JWT Bearer security scheme for Swagger UI
# ---------------------------------------------------------------------------


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Replace the auto-generated OAuth2PasswordBearer scheme with a clean
    # HTTP Bearer scheme so the Swagger "Authorize" button accepts a raw JWT.
    schema.setdefault("components", {})
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "Enter the JWT token obtained from POST /auth/login.\n\n"
                "Paste the token value only (without the 'Bearer ' prefix)."
            ),
        }
    }

    # Rewrite every operation that referenced the auto-generated
    # OAuth2PasswordBearer scheme to use BearerAuth instead.
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            if isinstance(operation, dict) and "security" in operation:
                operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
