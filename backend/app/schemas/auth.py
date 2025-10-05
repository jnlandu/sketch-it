"""
Authentication-related Pydantic schemas.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: Optional[str] = None


class RefreshToken(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict  # User information


class RegisterRequest(BaseModel):
    """Schema for registration request."""
    email: EmailStr
    password: str
    full_name: str


class RegisterResponse(BaseModel):
    """Schema for registration response."""
    message: str
    user_id: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""
    message: str


class PasswordResetConfirmRequest(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str


class PasswordResetConfirmResponse(BaseModel):
    """Schema for password reset confirmation response."""
    message: str


class EmailVerificationRequest(BaseModel):
    """Schema for email verification request."""
    token: str


class EmailVerificationResponse(BaseModel):
    """Schema for email verification response."""
    message: str


class ResendVerificationRequest(BaseModel):
    """Schema for resending email verification."""
    email: EmailStr


class ResendVerificationResponse(BaseModel):
    """Schema for resending email verification response."""
    message: str
