"""
Authentication service for handling auth-related business logic.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from supabase import Client

from app.config.database import get_db
from app.models.user import User
from app.core.security import PasswordManager, TokenManager
from app.core.exceptions import AuthenticationError, ValidationError


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_db()
    
    async def register_user(
        self,
        email: str,
        password: str,
        full_name: str
    ) -> User:
        """Register a new user."""
        from app.services.user_service import UserService
        
        user_service = UserService(self.db)
        return await user_service.create_user(
            email=email,
            password=password,
            full_name=full_name
        )
    
    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user with credentials."""
        from app.services.user_service import UserService
        
        user_service = UserService(self.db)
        return await user_service.authenticate_user(email, password)
    
    def create_access_token(self, user: User) -> str:
        """Create access token for user."""
        data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "type": "access"
        }
        return TokenManager.create_access_token(data)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token for user."""
        return TokenManager.create_refresh_token(user_id)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode token."""
        return TokenManager.verify_token(token)
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Create new access token from refresh token."""
        try:
            payload = self.verify_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token type")
            
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            
            # Get user to create new token
            from app.services.user_service import UserService
            user_service = UserService(self.db)
            user = await user_service.get_user_by_id(user_id)
            
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            # Create new tokens
            access_token = self.create_access_token(user)
            new_refresh_token = self.create_refresh_token(user.id)
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token
            }
            
        except Exception as e:
            raise AuthenticationError(f"Token refresh failed: {str(e)}")
    
    async def create_password_reset_token(self, email: str) -> Optional[str]:
        """Create password reset token for user."""
        from app.services.user_service import UserService
        from app.core.security import create_password_reset_token
        
        user_service = UserService(self.db)
        user = await user_service.get_user_by_email(email)
        
        if not user:
            return None
        
        return create_password_reset_token(user.id)
    
    async def reset_password_with_token(
        self,
        token: str,
        new_password: str
    ) -> bool:
        """Reset password using reset token."""
        from app.services.user_service import UserService
        from app.core.security import verify_password_reset_token
        
        user_id = verify_password_reset_token(token)
        if not user_id:
            raise AuthenticationError("Invalid or expired reset token")
        
        user_service = UserService(self.db)
        return await user_service.reset_password(user_id, new_password)
    
    async def verify_email(self, token: str) -> bool:
        """Verify user email with verification token."""
        try:
            payload = self.verify_token(token)
            
            if payload.get("type") != "email_verification":
                raise AuthenticationError("Invalid verification token type")
            
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            
            from app.services.user_service import UserService
            user_service = UserService(self.db)
            return await user_service.verify_user_email(user_id)
            
        except Exception as e:
            raise AuthenticationError(f"Email verification failed: {str(e)}")
    
    def create_email_verification_token(self, user_id: str) -> str:
        """Create email verification token."""
        data = {
            "sub": user_id,
            "type": "email_verification"
        }
        expire = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        data.update({"exp": expire})
        
        return TokenManager.create_access_token(data, expires_delta=timedelta(hours=24))