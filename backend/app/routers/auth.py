"""
Authentication router.

Endpoints:
  POST /auth/signup  — create a new user account
  POST /auth/login   — authenticate and receive a JWT
  GET  /auth/me      — return current authenticated user's profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, Token, UserResponse
from app.utils.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["Authentication"])


# ---------------------------------------------------------------------------
# POST /auth/signup
# ---------------------------------------------------------------------------


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> UserResponse:
    """
    Register a new user.

    - Validates email format and password strength (via Pydantic schema).
    - Rejects duplicate email addresses with HTTP 409.
    - Stores a bcrypt hash — never the plaintext password.
    - Returns the safe UserResponse (no password fields).
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    new_user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserResponse.model_validate(new_user)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive a JWT access token",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    """
    Authenticate a user with email and password.

    - Returns a JWT bearer token on success.
    - Returns HTTP 401 for invalid credentials (no detail that reveals
      whether the email or password was wrong).
    """
    user = db.query(User).filter(User.email == payload.email).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=user.id)
    return Token(access_token=access_token, token_type="bearer")


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user's profile",
)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Return the profile of the currently authenticated user.

    Requires a valid Bearer JWT in the Authorization header.
    Returns HTTP 401 if the token is missing, invalid, or expired.
    """
    return UserResponse.model_validate(current_user)
