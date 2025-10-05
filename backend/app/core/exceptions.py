"""
Custom exceptions for the Sketch It application.
"""

from typing import Optional, Dict, Any


class SketchItException(Exception):
    """Base exception class for Sketch It application."""
    
    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.headers = headers
        super().__init__(detail)


class AuthenticationError(SketchItException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            detail=detail,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(SketchItException):
    """Raised when user doesn't have permission."""
    
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            detail=detail,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )


class ValidationError(SketchItException):
    """Raised when input validation fails."""
    
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            detail=detail,
            status_code=422,
            error_code="VALIDATION_ERROR"
        )


class NotFoundError(SketchItException):
    """Raised when a resource is not found."""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            detail=detail,
            status_code=404,
            error_code="NOT_FOUND_ERROR"
        )


class ConflictError(SketchItException):
    """Raised when there's a conflict with existing data."""
    
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            detail=detail,
            status_code=409,
            error_code="CONFLICT_ERROR"
        )


class FileProcessingError(SketchItException):
    """Raised when file processing fails."""
    
    def __init__(self, detail: str = "File processing failed"):
        super().__init__(
            detail=detail,
            status_code=422,
            error_code="FILE_PROCESSING_ERROR"
        )


class StorageError(SketchItException):
    """Raised when storage operations fail."""
    
    def __init__(self, detail: str = "Storage operation failed"):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="STORAGE_ERROR"
        )


class RateLimitError(SketchItException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            detail=detail,
            status_code=429,
            error_code="RATE_LIMIT_ERROR"
        )


class SubscriptionError(SketchItException):
    """Raised when subscription-related issues occur."""
    
    def __init__(self, detail: str = "Subscription error"):
        super().__init__(
            detail=detail,
            status_code=402,
            error_code="SUBSCRIPTION_ERROR"
        )


class ImageProcessingError(SketchItException):
    """Raised when image processing fails."""
    
    def __init__(self, detail: str = "Image processing failed"):
        super().__init__(
            detail=detail,
            status_code=422,
            error_code="IMAGE_PROCESSING_ERROR"
        )
