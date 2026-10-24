"""Authentication routes under /api/v1/auth for registration and JWT login."""

from __future__ import annotations

import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserModel
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse
from app.utils.auth import create_access_token, get_current_user, get_password_hash, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description="Registers a new user account with email and password, hashing the password before storing in PostgreSQL.",
)
async def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new user account."""
    # Check if email is already registered
    existing_user = db.query(UserModel).filter(UserModel.email == payload.email).first()
    if existing_user:
        logger.warning(f"Registration attempt with existing email: {payload.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    # Hash password and persist user
    hashed_password = get_password_hash(payload.password)
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    new_user = UserModel(
        email=payload.email,
        hashed_password=hashed_password,
        created_at=created_at,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"Successfully registered user ID: {new_user.id} ({new_user.email})")
    return new_user


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User Login (OAuth2 Password Request Form)",
    description="Authenticates credentials via OAuth2 password request form for Swagger UI and API clients, returning a signed JWT access token.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate user with email (passed as username) and password via OAuth2 form data."""
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username/email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    logger.info(f"User {user.email} logged in successfully via OAuth2 form.")
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/token",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="OAuth2 Token Endpoint",
    description="OAuth2-compliant password form login endpoint alias.",
)
async def oauth2_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate user via OAuth2 password form (alias for /login)."""
    return await login(form_data=form_data, db=db)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User",
    description="Returns profile information for the authenticated user decoded from the JWT token.",
)
async def get_me(
    current_user: UserModel = Depends(get_current_user),
) -> UserResponse:
    """Return profile of the authenticated user."""
    return current_user
