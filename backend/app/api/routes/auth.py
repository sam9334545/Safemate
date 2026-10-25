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
from app.schemas.auth import (
    PasswordChangeRequest,
    PasswordChangeResponse,
    Token,
    TokenRefreshResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
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
    clean_email = str(payload.email).strip().lower()

    # Check if email is already registered
    existing_user = db.query(UserModel).filter(UserModel.email == clean_email).first()
    if existing_user:
        logger.warning(f"Registration attempt with existing email: {clean_email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    # Hash password and persist user
    hashed_password = get_password_hash(payload.password)
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    new_user = UserModel(
        email=clean_email,
        hashed_password=hashed_password,
        created_at=created_at,
        is_active=True,
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as exc:
        db.rollback()
        logger.error(f"Error persisting new user {clean_email}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user account. Email may already exist.",
        )

    logger.info(f"Successfully registered user ID: {new_user.id} ({new_user.email})")
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        is_guest=False,
        access_mode="personal_account",
    )


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
    clean_email = form_data.username.strip().lower()
    user = db.query(UserModel).filter(UserModel.email == clean_email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username/email: {clean_email}")
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

    is_guest = user.email.startswith("guest_") and user.email.endswith("@safemate.internal")
    access_token = create_access_token(data={
        "sub": user.email,
        "user_id": user.id,
        "is_guest": is_guest,
        "mode": "guest" if is_guest else "personal_account",
    })
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


@router.post(
    "/login-json",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User Login (JSON Payload)",
    description="Authenticates credentials via JSON body, returning a signed JWT access token.",
)
async def login_json(
    payload: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate user with email and password submitted as JSON."""
    clean_email = str(payload.email).strip().lower()
    user = db.query(UserModel).filter(UserModel.email == clean_email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning(f"Failed JSON login attempt for email: {clean_email}")
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

    is_guest = user.email.startswith("guest_") and user.email.endswith("@safemate.internal")
    access_token = create_access_token(data={
        "sub": user.email,
        "user_id": user.id,
        "is_guest": is_guest,
        "mode": "guest" if is_guest else "personal_account",
    })
    logger.info(f"User {user.email} logged in successfully via JSON.")
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/guest-session",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Issue Anonymous Guest Session Token",
    description="Issues an ephemeral, privacy-first JWT access token for emergency and fast feature access without prior registration.",
)
async def guest_session(
    db: Session = Depends(get_db),
) -> Token:
    """Issue a privacy-preserving temporary guest user token."""
    import secrets
    guest_suffix = secrets.token_hex(4)
    guest_email = f"guest_{guest_suffix}@safemate.internal"
    random_pw = secrets.token_urlsafe(16)
    hashed_pw = get_password_hash(random_pw)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    guest_user = UserModel(
        email=guest_email,
        hashed_password=hashed_pw,
        created_at=now_iso,
        is_active=True,
    )
    db.add(guest_user)
    db.commit()
    db.refresh(guest_user)

    access_token = create_access_token(data={
        "sub": guest_user.email,
        "user_id": guest_user.id,
        "is_guest": True,
        "mode": "guest",
    })
    logger.info(f"Guest session created: {guest_user.email}")
    return Token(access_token=access_token, token_type="bearer")


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
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        is_guest=getattr(current_user, "is_guest", False),
        access_mode=getattr(current_user, "access_mode", "personal_account"),
    )


@router.post(
    "/change-password",
    response_model=PasswordChangeResponse,
    status_code=status.HTTP_200_OK,
    summary="Change Authenticated User Password",
    description="Verifies the user's current password and securely updates to a new hashed password.",
)
async def change_password(
    payload: PasswordChangeRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PasswordChangeResponse:
    """Change account password for authenticated user."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password does not match.",
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    db.refresh(current_user)

    logger.info(f"User {current_user.email} successfully updated account password.")
    return PasswordChangeResponse(
        status="success",
        message="Password updated successfully. Please use your new password on next login.",
    )


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh JWT Access Token",
    description="Issues a fresh JWT access token with an extended expiration lifetime for the authenticated user.",
)
async def refresh_token(
    current_user: UserModel = Depends(get_current_user),
) -> TokenRefreshResponse:
    """Issue a fresh JWT token for authenticated active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    new_token = create_access_token(data={"sub": current_user.email, "user_id": current_user.id})
    return TokenRefreshResponse(access_token=new_token, token_type="bearer")


