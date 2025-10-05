"""
Common dependencies for API endpoints.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config.database import get_db, get_admin_db
from app.core.security import get_current_user, get_current_active_user, require_admin
from app.services.user_service import UserService
from app.services.sketch_service import SketchService
from app.services.subscription_service import SubscriptionService
from app.core.exceptions import AuthenticationError, RateLimitError


security = HTTPBearer()


def get_user_service() -> UserService:
    """Dependency to get user service."""
    return UserService()


def get_sketch_service() -> SketchService:
    """Dependency to get sketch service."""
    return SketchService()


def get_subscription_service() -> SubscriptionService:
    """Dependency to get subscription service."""
    return SubscriptionService()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current user ID from JWT token."""
    from app.core.security import get_current_user_id as _get_current_user_id
    return _get_current_user_id(credentials)


def get_optional_current_user_id(
    authorization: Optional[str] = None
) -> Optional[str]:
    """Get current user ID if provided, otherwise None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        from app.core.security import TokenManager
        token = authorization.replace("Bearer ", "")
        payload = TokenManager.verify_token(token)
        return payload.get("sub")
    except Exception:
        return None


def verify_sketch_ownership(
    sketch_id: str,
    current_user_id: str = Depends(get_current_user_id),
    sketch_service: SketchService = Depends(get_sketch_service)
):
    """Verify that the current user owns the sketch."""
    async def _verify():
        sketch = await sketch_service.get_sketch_by_id(sketch_id)
        if not sketch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sketch not found"
            )
        
        if sketch.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this sketch"
            )
        
        return sketch
    
    return _verify


class RateLimiter:
    """Simple rate limiter for API endpoints."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # In production, use Redis
    
    async def __call__(self, request: Request):
        import time
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self.requests = {
            ip: timestamps for ip, timestamps in self.requests.items()
            if any(t > current_time - self.window_seconds for t in timestamps)
        }
        
        # Check rate limit
        if client_ip in self.requests:
            recent_requests = [
                t for t in self.requests[client_ip]
                if t > current_time - self.window_seconds
            ]
            
            if len(recent_requests) >= self.max_requests:
                raise RateLimitError(
                    f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds"
                )
            
            self.requests[client_ip] = recent_requests + [current_time]
        else:
            self.requests[client_ip] = [current_time]


# Rate limiter instances
upload_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)  # 5 uploads per minute
auth_rate_limiter = RateLimiter(max_requests=10, window_seconds=300)  # 10 auth attempts per 5 minutes
general_rate_limiter = RateLimiter(max_requests=60, window_seconds=60)  # 60 general requests per minute


def validate_pagination(
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> dict:
    """Validate and normalize pagination parameters."""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0"
        )
    
    if per_page < 1 or per_page > max_per_page:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Per page must be between 1 and {max_per_page}"
        )
    
    return {
        'page': page,
        'per_page': per_page,
        'offset': (page - 1) * per_page
    }


def validate_file_upload(file_size: int, max_size: int = 10 * 1024 * 1024):
    """Validate file upload size."""
    if file_size > max_size:
        max_mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_mb}MB"
        )


def get_client_info(request: Request) -> dict:
    """Extract client information from request."""
    return {
        'ip': request.client.host if request.client else "unknown",
        'user_agent': request.headers.get('user-agent', 'unknown'),
        'referer': request.headers.get('referer'),
        'forwarded_for': request.headers.get('x-forwarded-for'),
        'real_ip': request.headers.get('x-real-ip')
    }
