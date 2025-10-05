"""
User management endpoints.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

from app.schemas.user import (
    UserResponse, UserUpdate, UserPasswordChange, UserProfile
)
from app.services.user_service import UserService
from app.api.deps import (
    get_user_service, get_current_user_id, get_current_active_user,
    require_admin, validate_pagination, general_rate_limiter, get_client_info
)
from app.core.exceptions import (
    NotFoundError, ValidationError, AuthenticationError, AuthorizationError
)
from app.models.user import UserRole

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get current user profile."""
    return UserResponse(**current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
    _: None = Depends(general_rate_limiter)
):
    """Update current user profile."""
    try:
        updated_user = await user_service.update_user(
            user_id=current_user_id,
            update_data=user_update.dict(exclude_unset=True)
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**updated_user.__dict__)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/me/change-password")
async def change_password(
    password_change: UserPasswordChange,
    current_user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
    _: None = Depends(general_rate_limiter)
):
    """Change current user's password."""
    try:
        success = await user_service.update_password(
            user_id=current_user_id,
            current_password=password_change.current_password,
            new_password=password_change.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return {"message": "Password updated successfully"}
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.put("/me/profile", response_model=UserResponse)
async def update_user_profile(
    profile_update: UserProfile,
    current_user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
    _: None = Depends(general_rate_limiter)
):
    """Update user profile information."""
    try:
        updated_user = await user_service.update_user(
            user_id=current_user_id,
            update_data=profile_update.dict(exclude_unset=True)
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**updated_user.__dict__)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get user by ID (public profile)."""
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return public profile unless it's the same user
        if user_id == current_user_id:
            return UserResponse(**user.__dict__)
        else:
            # Return limited public information
            public_profile = user.get_public_profile()
            return UserResponse(**public_profile)
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/", response_model=Dict[str, Any])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = Query(None, max_length=100),
    role: UserRole = Query(None),
    is_active: bool = Query(None),
    user_service: UserService = Depends(get_user_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """List users (admin only)."""
    try:
        pagination = validate_pagination(page, per_page)
        
        result = await user_service.get_users_list(
            page=pagination['page'],
            per_page=pagination['per_page'],
            search=search,
            role=role,
            is_active=is_active
        )
        
        # Convert users to response format
        users_response = [
            UserResponse(**user.__dict__) for user in result['users']
        ]
        
        return {
            'users': users_response,
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'total_pages': result['total_pages']
        }
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """Deactivate user account (admin only)."""
    try:
        success = await user_service.deactivate_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deactivated successfully"}
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """Activate user account (admin only)."""
    try:
        updated_user = await user_service.update_user(
            user_id=user_id,
            update_data={'is_active': True}
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User activated successfully"}
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/{user_id}/verify-email")
async def verify_user_email(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """Verify user email (admin only)."""
    try:
        success = await user_service.verify_user_email(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User email verified successfully"}
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/stats/overview")
async def get_user_stats(
    user_service: UserService = Depends(get_user_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """Get user statistics overview (admin only)."""
    try:
        # This would be implemented with proper aggregation queries
        # For now, return placeholder data
        return {
            "total_users": 0,
            "active_users": 0,
            "verified_users": 0,
            "premium_users": 0,
            "new_users_this_month": 0,
            "users_by_role": {
                "user": 0,
                "premium": 0,
                "admin": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )
