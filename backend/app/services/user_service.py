"""
User service for handling user-related business logic.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from supabase import Client

from app.config.database import get_db, get_admin_db
from app.models.user import User, UserRole, SubscriptionType
from app.core.security import PasswordManager
from app.core.exceptions import (
    NotFoundError, ConflictError, ValidationError, AuthenticationError
)


class UserService:
    """Service class for user operations."""
    
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_db()
        self.admin_db = get_admin_db()
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.USER
    ) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise ConflictError("User with this email already exists")
        
        # Hash password
        hashed_password = PasswordManager.hash_password(password)
        
        # Create user data
        user_data = {
            'id': str(uuid.uuid4()),
            'email': email.lower(),
            'full_name': full_name,
            'hashed_password': hashed_password,
            'role': role.value,
            'is_active': True,
            'is_verified': False,
            'subscription_type': SubscriptionType.FREE.value,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
        }
        
        # Insert user into database
        try:
            result = self.db.table('users').insert(user_data).execute()
            if result.data:
                user = User.from_dict(result.data[0])
                
                # Create default subscription
                await self._create_default_subscription(user.id)
                
                return user
            else:
                raise ValidationError("Failed to create user")
        except Exception as e:
            if "duplicate key" in str(e).lower():
                raise ConflictError("User with this email already exists")
            raise ValidationError(f"Failed to create user: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            result = self.db.table('users').select(
                '*, sketches_count:sketches!user_id(count)'
            ).eq('id', user_id).execute()
            
            if result.data:
                user_data = result.data[0]
                # Handle sketches count from aggregation
                if 'sketches_count' in user_data and user_data['sketches_count']:
                    user_data['sketches_count'] = user_data['sketches_count'][0]['count']
                else:
                    user_data['sketches_count'] = 0
                
                return User.from_dict(user_data)
            return None
        except Exception as e:
            raise ValidationError(f"Failed to get user: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            result = self.db.table('users').select('*').eq(
                'email', email.lower()
            ).execute()
            
            if result.data:
                return User.from_dict(result.data[0])
            return None
        except Exception as e:
            raise ValidationError(f"Failed to get user: {str(e)}")
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not PasswordManager.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            raise AuthenticationError("User account is deactivated")
        
        # Update last login
        await self.update_last_login(user.id)
        
        return user
    
    async def update_user(
        self,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[User]:
        """Update user information."""
        # Remove None values and prepare update data
        clean_data = {k: v for k, v in update_data.items() if v is not None}
        clean_data['updated_at'] = datetime.utcnow().isoformat()
        
        try:
            result = self.db.table('users').update(clean_data).eq(
                'id', user_id
            ).execute()
            
            if result.data:
                return User.from_dict(result.data[0])
            return None
        except Exception as e:
            raise ValidationError(f"Failed to update user: {str(e)}")
    
    async def update_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """Update user password."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Verify current password
        if not PasswordManager.verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        
        # Hash new password
        hashed_password = PasswordManager.hash_password(new_password)
        
        # Update password
        update_data = {
            'hashed_password': hashed_password,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        try:
            result = self.db.table('users').update(update_data).eq(
                'id', user_id
            ).execute()
            return bool(result.data)
        except Exception as e:
            raise ValidationError(f"Failed to update password: {str(e)}")
    
    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """Reset user password (admin operation)."""
        # Hash new password
        hashed_password = PasswordManager.hash_password(new_password)
        
        # Update password
        update_data = {
            'hashed_password': hashed_password,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        try:
            result = self.admin_db.table('users').update(update_data).eq(
                'id', user_id
            ).execute()
            return bool(result.data)
        except Exception as e:
            raise ValidationError(f"Failed to reset password: {str(e)}")
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        update_data = {
            'last_login': datetime.utcnow().isoformat()
        }
        
        try:
            result = self.db.table('users').update(update_data).eq(
                'id', user_id
            ).execute()
            return bool(result.data)
        except Exception as e:
            # Don't raise exception for non-critical operation
            return False
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account."""
        update_data = {
            'is_active': False,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        try:
            result = self.admin_db.table('users').update(update_data).eq(
                'id', user_id
            ).execute()
            return bool(result.data)
        except Exception as e:
            raise ValidationError(f"Failed to deactivate user: {str(e)}")
    
    async def verify_user_email(self, user_id: str) -> bool:
        """Verify user's email address."""
        update_data = {
            'is_verified': True,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        try:
            result = self.db.table('users').update(update_data).eq(
                'id', user_id
            ).execute()
            return bool(result.data)
        except Exception as e:
            raise ValidationError(f"Failed to verify email: {str(e)}")
    
    async def get_users_list(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get paginated list of users (admin operation)."""
        offset = (page - 1) * per_page
        
        # Build query
        query = self.admin_db.table('users').select(
            '*, sketches_count:sketches!user_id(count)'
        )
        
        # Apply filters
        if search:
            query = query.or_(
                f'full_name.ilike.%{search}%,email.ilike.%{search}%'
            )
        
        if role:
            query = query.eq('role', role.value)
        
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        # Get total count
        count_result = query.execute()
        total = len(count_result.data) if count_result.data else 0
        
        # Get paginated results
        result = query.order('created_at', desc=True).range(
            offset, offset + per_page - 1
        ).execute()
        
        users = []
        if result.data:
            for user_data in result.data:
                # Handle sketches count from aggregation
                if 'sketches_count' in user_data and user_data['sketches_count']:
                    user_data['sketches_count'] = user_data['sketches_count'][0]['count']
                else:
                    user_data['sketches_count'] = 0
                
                users.append(User.from_dict(user_data))
        
        return {
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    
    async def _create_default_subscription(self, user_id: str):
        """Create default free subscription for new user."""
        from app.services.subscription_service import SubscriptionService
        
        subscription_service = SubscriptionService()
        await subscription_service.create_subscription(
            user_id=user_id,
            plan=SubscriptionType.FREE
        )
