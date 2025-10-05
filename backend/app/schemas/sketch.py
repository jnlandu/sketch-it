"""
Sketch-related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class SketchStatus(str, Enum):
    """Sketch processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SketchStyle(str, Enum):
    """Available sketch styles."""
    PENCIL = "pencil"
    CHARCOAL = "charcoal"
    INK = "ink"
    WATERCOLOR = "watercolor"


class SketchBase(BaseModel):
    """Base sketch schema with common fields."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    style: SketchStyle = Field(default=SketchStyle.PENCIL)
    is_public: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list, max_items=10)
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags format."""
        if not v:
            return v
        
        # Remove empty tags and limit length
        cleaned_tags = [tag.strip()[:50] for tag in v if tag.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in cleaned_tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)
        
        return unique_tags[:10]


class SketchCreate(SketchBase):
    """Schema for sketch creation."""
    pass


class SketchUpdate(BaseModel):
    """Schema for sketch updates."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = Field(None, max_items=10)
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags format."""
        if v is None:
            return v
        
        # Remove empty tags and limit length
        cleaned_tags = [tag.strip()[:50] for tag in v if tag.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in cleaned_tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)
        
        return unique_tags[:10]


class SketchResponse(SketchBase):
    """Schema for sketch response."""
    id: str
    user_id: str
    status: SketchStatus
    original_url: Optional[str] = None
    sketch_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    processing_time: Optional[float] = None  # seconds
    views_count: int = Field(default=0)
    likes_count: int = Field(default=0)
    downloads_count: int = Field(default=0)
    created_at: datetime
    updated_at: datetime
    user_full_name: Optional[str] = None  # For public listings
    
    class Config:
        from_attributes = True


class SketchListResponse(BaseModel):
    """Schema for sketch list response."""
    sketches: List[SketchResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class SketchUpload(BaseModel):
    """Schema for sketch upload metadata."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    style: SketchStyle = Field(default=SketchStyle.PENCIL)
    is_public: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list, max_items=10)


class SketchProcessingOptions(BaseModel):
    """Schema for sketch processing options."""
    style: SketchStyle = Field(default=SketchStyle.PENCIL)
    intensity: float = Field(default=1.0, ge=0.1, le=2.0)
    contrast: float = Field(default=1.0, ge=0.1, le=2.0)
    blur_kernel: int = Field(default=5, ge=3, le=15)
    edge_threshold1: int = Field(default=50, ge=10, le=200)
    edge_threshold2: int = Field(default=150, ge=50, le=300)
    
    @validator('blur_kernel')
    def validate_blur_kernel(cls, v):
        """Ensure blur kernel is odd."""
        if v % 2 == 0:
            v += 1
        return v


class SketchStats(BaseModel):
    """Schema for sketch statistics."""
    total_sketches: int
    public_sketches: int
    private_sketches: int
    total_views: int
    total_likes: int
    total_downloads: int
    average_processing_time: Optional[float] = None
    most_popular_style: Optional[str] = None


class SketchSearchQuery(BaseModel):
    """Schema for sketch search query."""
    query: Optional[str] = Field(None, max_length=100)
    style: Optional[SketchStyle] = None
    tags: Optional[List[str]] = Field(None, max_items=5)
    user_id: Optional[str] = None
    is_public: bool = Field(default=True)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at", regex="^(created_at|updated_at|views_count|likes_count|title)$")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$")


class SketchLike(BaseModel):
    """Schema for sketch like/unlike."""
    liked: bool


class SketchDownload(BaseModel):
    """Schema for sketch download response."""
    download_url: str
    expires_at: datetime
