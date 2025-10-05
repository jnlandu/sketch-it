"""
Subscription database model for Supabase.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class SubscriptionPlan(str, Enum):
    """Available subscription plans."""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


@dataclass
class Subscription:
    """Subscription model for database operations."""
    
    id: str
    user_id: str
    plan: SubscriptionPlan = SubscriptionPlan.FREE
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    
    # Subscription details
    started_at: datetime = None
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Usage tracking
    daily_sketches_count: int = 0
    monthly_sketches_count: int = 0
    total_sketches_count: int = 0
    last_usage_date: Optional[datetime] = None
    
    # Payment information
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "USD"
    
    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert subscription to dictionary for database operations."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan': self.plan.value if isinstance(self.plan, SubscriptionPlan) else self.plan,
            'status': self.status.value if isinstance(self.status, SubscriptionStatus) else self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'daily_sketches_count': self.daily_sketches_count,
            'monthly_sketches_count': self.monthly_sketches_count,
            'total_sketches_count': self.total_sketches_count,
            'last_usage_date': self.last_usage_date.isoformat() if self.last_usage_date else None,
            'stripe_subscription_id': self.stripe_subscription_id,
            'stripe_customer_id': self.stripe_customer_id,
            'amount': self.amount,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subscription':
        """Create subscription from database row."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            plan=SubscriptionPlan(data.get('plan', 'free')),
            status=SubscriptionStatus(data.get('status', 'active')),
            started_at=datetime.fromisoformat(data['started_at'].replace('Z', '+00:00')) if data.get('started_at') else None,
            expires_at=datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00')) if data.get('expires_at') else None,
            cancelled_at=datetime.fromisoformat(data['cancelled_at'].replace('Z', '+00:00')) if data.get('cancelled_at') else None,
            daily_sketches_count=data.get('daily_sketches_count', 0),
            monthly_sketches_count=data.get('monthly_sketches_count', 0),
            total_sketches_count=data.get('total_sketches_count', 0),
            last_usage_date=datetime.fromisoformat(data['last_usage_date'].replace('Z', '+00:00')) if data.get('last_usage_date') else None,
            stripe_subscription_id=data.get('stripe_subscription_id'),
            stripe_customer_id=data.get('stripe_customer_id'),
            amount=data.get('amount'),
            currency=data.get('currency', 'USD'),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')) if data.get('updated_at') else None,
        )
    
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == SubscriptionStatus.ACTIVE and (
            not self.expires_at or self.expires_at > datetime.utcnow()
        )
    
    def is_expired(self) -> bool:
        """Check if subscription is expired."""
        return self.expires_at and self.expires_at <= datetime.utcnow()
    
    def days_until_expiry(self) -> Optional[int]:
        """Get days until subscription expires."""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def can_create_sketch(self) -> bool:
        """Check if user can create a sketch based on subscription limits."""
        if not self.is_active():
            return False
        
        if self.plan == SubscriptionPlan.FREE:
            return self.daily_sketches_count < 5
        elif self.plan == SubscriptionPlan.PREMIUM:
            return self.daily_sketches_count < 100
        else:  # Enterprise
            return True
    
    def get_daily_limit(self) -> int:
        """Get daily sketch limit for the subscription plan."""
        if self.plan == SubscriptionPlan.FREE:
            return 5
        elif self.plan == SubscriptionPlan.PREMIUM:
            return 100
        else:  # Enterprise
            return 10000  # Very high limit
    
    def get_monthly_limit(self) -> int:
        """Get monthly sketch limit for the subscription plan."""
        if self.plan == SubscriptionPlan.FREE:
            return 50
        elif self.plan == SubscriptionPlan.PREMIUM:
            return 3000
        else:  # Enterprise
            return 100000  # Very high limit
    
    def reset_daily_count(self):
        """Reset daily sketches count."""
        self.daily_sketches_count = 0
    
    def reset_monthly_count(self):
        """Reset monthly sketches count."""
        self.monthly_sketches_count = 0


# Database table schema for Supabase
SUBSCRIPTION_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(20) DEFAULT 'free' CHECK (plan IN ('free', 'premium', 'enterprise')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'cancelled', 'expired', 'pending')),
    
    -- Subscription timeline
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    daily_sketches_count INTEGER DEFAULT 0,
    monthly_sketches_count INTEGER DEFAULT 0,
    total_sketches_count INTEGER DEFAULT 0,
    last_usage_date DATE,
    
    -- Payment information
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, plan),
    CONSTRAINT valid_amount CHECK (amount IS NULL OR amount >= 0)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_plan ON subscriptions(plan);
CREATE INDEX IF NOT EXISTS idx_subscriptions_expires_at ON subscriptions(expires_at);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);

-- Create updated_at trigger
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create usage tracking table
CREATE TABLE IF NOT EXISTS subscription_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
    sketches_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_subscription_usage_user_id ON subscription_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_usage_date ON subscription_usage(usage_date);

-- Function to reset daily counts
CREATE OR REPLACE FUNCTION reset_daily_subscription_counts()
RETURNS void AS $$
BEGIN
    UPDATE subscriptions SET daily_sketches_count = 0;
END;
$$ LANGUAGE plpgsql;

-- Function to reset monthly counts
CREATE OR REPLACE FUNCTION reset_monthly_subscription_counts()
RETURNS void AS $$
BEGIN
    UPDATE subscriptions SET monthly_sketches_count = 0;
END;
$$ LANGUAGE plpgsql;

-- Function to update subscription status based on expiry
CREATE OR REPLACE FUNCTION update_expired_subscriptions()
RETURNS void AS $$
BEGIN
    UPDATE subscriptions 
    SET status = 'expired' 
    WHERE expires_at <= NOW() 
    AND status = 'active';
END;
$$ LANGUAGE plpgsql;
"""
