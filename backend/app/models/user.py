"""
User database model for Supabase.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class SubscriptionType(str, Enum):
    """Subscription types."""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class User:
    """User model for database operations."""
    
    id: str
    email: str
    full_name: str
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    role: UserRole = UserRole.USER
    subscription_type: SubscriptionType = SubscriptionType.FREE
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    last_login: Optional[datetime] = None
    
    # Computed fields
    sketches_count: int = 0
    total_views: int = 0
    total_likes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for database operations."""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'hashed_password': self.hashed_password,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'role': self.role.value if isinstance(self.role, UserRole) else self.role,
            'subscription_type': self.subscription_type.value if isinstance(self.subscription_type, SubscriptionType) else self.subscription_type,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'website': self.website,
            'location': self.location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from database row."""
        return cls(
            id=data.get('id'),
            email=data.get('email'),
            full_name=data.get('full_name'),
            hashed_password=data.get('hashed_password'),
            is_active=data.get('is_active', True),
            is_verified=data.get('is_verified', False),
            role=UserRole(data.get('role', 'user')),
            subscription_type=SubscriptionType(data.get('subscription_type', 'free')),
            avatar_url=data.get('avatar_url'),
            bio=data.get('bio'),
            website=data.get('website'),
            location=data.get('location'),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')) if data.get('updated_at') else None,
            last_login=datetime.fromisoformat(data['last_login'].replace('Z', '+00:00')) if data.get('last_login') else None,
            sketches_count=data.get('sketches_count', 0),
            total_views=data.get('total_views', 0),
            total_likes=data.get('total_likes', 0),
        )
    
    def is_premium_user(self) -> bool:
        """Check if user has premium subscription."""
        return self.subscription_type in [SubscriptionType.PREMIUM, SubscriptionType.ENTERPRISE]
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    def can_create_sketch(self, daily_count: int) -> bool:
        """Check if user can create more sketches today."""
        if self.subscription_type == SubscriptionType.FREE:
            return daily_count < 5  # Free tier limit
        elif self.subscription_type == SubscriptionType.PREMIUM:
            return daily_count < 100  # Premium tier limit
        else:  # Enterprise
            return True  # No limit
    
    def get_public_profile(self) -> Dict[str, Any]:
        """Get public profile information."""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'website': self.website,
            'location': self.location,
            'sketches_count': self.sketches_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# Database table schema for Supabase
USER_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'premium', 'admin')),
    subscription_type VARCHAR(20) DEFAULT 'free' CHECK (subscription_type IN ('free', 'premium', 'enterprise')),
    avatar_url TEXT,
    bio TEXT,
    website VARCHAR(255),
    location VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_subscription_type ON users(subscription_type);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""
