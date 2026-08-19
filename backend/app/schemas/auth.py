"""
Pydantic schemas for authentication endpoints.

These schemas define the shape of request/response bodies.
IMPORTANT: Never include password_hash in any response schema.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class SignupRequest(BaseModel):
    """Request body for POST /auth/signup."""

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Response body for successful login."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """
    Safe user representation returned by API responses.
    Never includes password or password_hash.
    """

    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
