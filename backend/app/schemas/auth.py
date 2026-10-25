"""Pydantic schemas for User Authentication and JWT tokens."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

try:
    from pydantic import EmailStr
    from pydantic.networks import import_email_validator
    import_email_validator()
except Exception:
    EmailStr = str


class UserCreate(BaseModel):
    """Payload for user registration."""

    email: EmailStr = Field(
        ...,
        description="Valid email address for the user account",
        examples=["user@safemate.org"],
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Account password (minimum 6 characters)",
        examples=["SecurePass123!"],
    )
    full_name: Optional[str] = Field(
        default=None,
        description="Optional full name or alias",
        examples=["Priya Sharma"],
    )


class UserLogin(BaseModel):
    """Payload for user login via JSON body."""

    email: EmailStr = Field(
        ...,
        description="Registered account email address",
        examples=["user@safemate.org"],
    )
    password: str = Field(
        ...,
        description="Account password",
        examples=["SecurePass123!"],
    )


class Token(BaseModel):
    """Response containing JWT access token."""

    access_token: str = Field(..., description="JWT Bearer access token string")
    token_type: str = Field(default="bearer", description="Token type specification")


class TokenData(BaseModel):
    """Internal schema for decoded JWT token payload."""

    email: Optional[str] = None


class UserResponse(BaseModel):
    """Response schema representing a user profile."""

    id: int
    email: EmailStr
    is_active: bool
    created_at: str
    is_guest: bool = False
    access_mode: str = "personal_account"

    model_config = {
        "from_attributes": True,
    }


class PasswordChangeRequest(BaseModel):
    """Payload for changing authenticated user password."""

    current_password: str = Field(..., min_length=1, description="Current existing password")
    new_password: str = Field(..., min_length=6, description="New password (minimum 6 characters)")


class PasswordChangeResponse(BaseModel):
    """Response payload confirming password change."""

    status: str = Field(default="success", description="Status confirmation")
    message: str = Field(
        default="Password updated successfully.",
        description="Status explanation message",
    )


class TokenRefreshResponse(BaseModel):
    """Response returning refreshed access token."""

    access_token: str = Field(..., description="Fresh JWT access token")
    token_type: str = Field(default="bearer", description="Token type specification")

