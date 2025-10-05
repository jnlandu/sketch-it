"""
Authentication endpoints for user registration, login, and token management.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.schemas.auth import (
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    RefreshToken, Token, PasswordResetRequest, PasswordResetResponse,
    PasswordResetConfirmRequest, PasswordResetConfirmResponse
)
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.api.deps import get_user_service, auth_rate_limiter, get_client_info
from app.core.security import TokenManager
from app.core.exceptions import AuthenticationError, ValidationError, ConflictError
from app.config.settings import settings

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    client_info: dict = Depends(get_client_info),
    user_service: UserService = Depends(get_user_service),
    _: None = Depends(auth_rate_limiter)
):
    """Register a new user account."""
    try:
        # Create new user
        user = await user_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        return RegisterResponse(
            message="User registered successfully. Please check your email for verification.",
            user_id=user.id
        )
        
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    client_info: dict = Depends(get_client_info),
    user_service: UserService = Depends(get_user_service),
    _: None = Depends(auth_rate_limiter)
):
    """Authenticate user and return access token."""
    try:
        # Authenticate user
        user = await user_service.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token = TokenManager.create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )
        
        # Create refresh token
        refresh_token = TokenManager.create_refresh_token(user.id)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "subscription_type": user.subscription_type
            }
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshToken,
    user_service: UserService = Depends(get_user_service)
):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        payload = TokenManager.verify_token(request.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = TokenManager.create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )
        
        # Create new refresh token
        new_refresh_token = TokenManager.create_refresh_token(user.id)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/password-reset", response_model=PasswordResetResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    user_service: UserService = Depends(get_user_service),
    _: None = Depends(auth_rate_limiter)
):
    """Request password reset for a user."""
    try:
        # Check if user exists
        user = await user_service.get_user_by_email(request.email)
        
        # Always return success to prevent email enumeration
        if user:
            # In a real implementation, send email with reset token
            # For now, just log the token
            from app.core.security import create_password_reset_token
            reset_token = create_password_reset_token(user.id)
            # TODO: Send email with reset_token
            print(f"Password reset token for {user.email}: {reset_token}")
        
        return PasswordResetResponse(
            message="If an account with this email exists, a password reset link has been sent."
        )
        
    except Exception as e:
        # Always return success for security
        return PasswordResetResponse(
            message="If an account with this email exists, a password reset link has been sent."
        )


@router.post("/password-reset/confirm", response_model=PasswordResetConfirmResponse)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Confirm password reset with token."""
    try:
        from app.core.security import verify_password_reset_token
        
        # Verify reset token
        user_id = verify_password_reset_token(request.token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Reset password
        success = await user_service.reset_password(user_id, request.new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )
        
        return PasswordResetConfirmResponse(
            message="Password has been reset successfully."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post("/logout")
async def logout():
    """Logout user (invalidate token)."""
    # In a stateless JWT implementation, logout is handled client-side
    # In production, you might want to maintain a blacklist of tokens
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserResponse(**current_user)
