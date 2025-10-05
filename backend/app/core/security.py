"""
Security utilities for authentication and authorization.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config.settings import settings
from app.core.exceptions import AuthenticationError, AuthorizationError

# Security scheme
security = HTTPBearer()


class PasswordManager:
    """Handle password hashing and verification."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )


class TokenManager:
    """Handle JWT token creation and validation."""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        
        return jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a refresh token."""
        data = {
            "sub": user_id,
            "type": "refresh"
        }
        expire = datetime.utcnow() + timedelta(days=30)
        data.update({"exp": expire})
        
        return jwt.encode(
            data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current user ID from JWT token."""
    try:
        payload = TokenManager.verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        # Check if token is not expired
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise AuthenticationError("Token expired")
        
        return user_id
        
    except JWTError:
        raise AuthenticationError("Could not validate credentials")


async def get_current_user(
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get current user from database."""
    from app.services.user_service import UserService
    
    user_service = UserService()
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        raise AuthenticationError("User not found")
    
    return user


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current active user."""
    if not current_user.get("is_active", True):
        raise AuthorizationError("Inactive user")
    
    return current_user


class RoleChecker:
    """Check user roles and permissions."""
    
    def __init__(self, allowed_roles: list = None):
        self.allowed_roles = allowed_roles or []
    
    def __call__(self, current_user: Dict[str, Any] = Depends(get_current_active_user)):
        if self.allowed_roles and current_user.get("role") not in self.allowed_roles:
            raise AuthorizationError(
                f"Operation requires one of these roles: {', '.join(self.allowed_roles)}"
            )
        return current_user


# Common role checkers
require_admin = RoleChecker(["admin"])
require_premium = RoleChecker(["premium", "admin"])


def create_password_reset_token(user_id: str) -> str:
    """Create a password reset token."""
    data = {
        "sub": user_id,
        "type": "password_reset"
    }
    expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
    data.update({"exp": expire})
    
    return jwt.encode(
        data,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return user ID."""
    try:
        payload = TokenManager.verify_token(token)
        
        if payload.get("type") != "password_reset":
            return None
        
        return payload.get("sub")
    except AuthenticationError:
        return None
