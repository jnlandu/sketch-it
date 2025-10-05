"""
Application settings and configuration management.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    APP_NAME: str = "Sketch It API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"], 
        env="ALLOWED_HOSTS"
    )
    
    # Security settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    
    # Database settings (Supabase)
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_KEY")
    
    # Storage settings
    STORAGE_BUCKET: str = Field(default="sketch-storage", env="STORAGE_BUCKET")
    MAX_FILE_SIZE: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        env="ALLOWED_IMAGE_TYPES"
    )
    
    # Upload paths
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    STORAGE_DIR: str = Field(default="storage", env="STORAGE_DIR")
    
    # Email settings (optional)
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: Optional[int] = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    
    # Image processing settings
    THUMBNAIL_SIZE: tuple = (200, 200)
    SKETCH_QUALITY: int = Field(default=85, env="SKETCH_QUALITY")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Subscription limits
    FREE_TIER_DAILY_LIMIT: int = Field(default=5, env="FREE_TIER_DAILY_LIMIT")
    PREMIUM_TIER_DAILY_LIMIT: int = Field(default=100, env="PREMIUM_TIER_DAILY_LIMIT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.STORAGE_DIR, exist_ok=True)
        os.makedirs(f"{self.STORAGE_DIR}/original", exist_ok=True)
        os.makedirs(f"{self.STORAGE_DIR}/sketches", exist_ok=True)
        os.makedirs(f"{self.STORAGE_DIR}/thumbnails", exist_ok=True)
        os.makedirs("logs", exist_ok=True)


# Create global settings instance
settings = Settings()
