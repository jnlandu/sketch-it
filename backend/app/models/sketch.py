"""
Sketch database model for Supabase.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
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


@dataclass
class Sketch:
    """Sketch model for database operations."""
    
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    style: SketchStyle = SketchStyle.PENCIL
    status: SketchStatus = SketchStatus.PENDING
    is_public: bool = False
    tags: List[str] = None
    
    # File information
    original_filename: Optional[str] = None
    original_url: Optional[str] = None
    sketch_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None
    
    # Image metadata
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    file_format: Optional[str] = None
    
    # Processing metadata
    processing_time: Optional[float] = None
    processing_options: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Engagement metrics
    views_count: int = 0
    likes_count: int = 0
    downloads_count: int = 0
    
    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None
    processed_at: Optional[datetime] = None
    
    # User information (for joins)
    user_full_name: Optional[str] = None
    user_avatar_url: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sketch to dictionary for database operations."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'style': self.style.value if isinstance(self.style, SketchStyle) else self.style,
            'status': self.status.value if isinstance(self.status, SketchStatus) else self.status,
            'is_public': self.is_public,
            'tags': self.tags or [],
            'original_filename': self.original_filename,
            'original_url': self.original_url,
            'sketch_url': self.sketch_url,
            'thumbnail_url': self.thumbnail_url,
            'file_size': self.file_size,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'file_format': self.file_format,
            'processing_time': self.processing_time,
            'processing_options': self.processing_options or {},
            'error_message': self.error_message,
            'views_count': self.views_count,
            'likes_count': self.likes_count,
            'downloads_count': self.downloads_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sketch':
        """Create sketch from database row."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            title=data.get('title'),
            description=data.get('description'),
            style=SketchStyle(data.get('style', 'pencil')),
            status=SketchStatus(data.get('status', 'pending')),
            is_public=data.get('is_public', False),
            tags=data.get('tags', []),
            original_filename=data.get('original_filename'),
            original_url=data.get('original_url'),
            sketch_url=data.get('sketch_url'),
            thumbnail_url=data.get('thumbnail_url'),
            file_size=data.get('file_size'),
            image_width=data.get('image_width'),
            image_height=data.get('image_height'),
            file_format=data.get('file_format'),
            processing_time=data.get('processing_time'),
            processing_options=data.get('processing_options', {}),
            error_message=data.get('error_message'),
            views_count=data.get('views_count', 0),
            likes_count=data.get('likes_count', 0),
            downloads_count=data.get('downloads_count', 0),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')) if data.get('updated_at') else None,
            processed_at=datetime.fromisoformat(data['processed_at'].replace('Z', '+00:00')) if data.get('processed_at') else None,
            user_full_name=data.get('user_full_name'),
            user_avatar_url=data.get('user_avatar_url'),
        )
    
    def is_processing_complete(self) -> bool:
        """Check if sketch processing is complete."""
        return self.status == SketchStatus.COMPLETED
    
    def is_processing_failed(self) -> bool:
        """Check if sketch processing failed."""
        return self.status == SketchStatus.FAILED
    
    def can_be_viewed_by(self, user_id: Optional[str]) -> bool:
        """Check if sketch can be viewed by user."""
        if self.is_public:
            return True
        return user_id == self.user_id
    
    def get_public_info(self) -> Dict[str, Any]:
        """Get public information about the sketch."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'style': self.style,
            'tags': self.tags,
            'sketch_url': self.sketch_url,
            'thumbnail_url': self.thumbnail_url,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'views_count': self.views_count,
            'likes_count': self.likes_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_full_name': self.user_full_name,
            'user_avatar_url': self.user_avatar_url,
        }


# Database table schema for Supabase
SKETCH_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS sketches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    style VARCHAR(20) DEFAULT 'pencil' CHECK (style IN ('pencil', 'charcoal', 'ink', 'watercolor')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    is_public BOOLEAN DEFAULT FALSE,
    tags TEXT[] DEFAULT '{}',
    
    -- File information
    original_filename VARCHAR(255),
    original_url TEXT,
    sketch_url TEXT,
    thumbnail_url TEXT,
    file_size INTEGER,
    
    -- Image metadata
    image_width INTEGER,
    image_height INTEGER,
    file_format VARCHAR(10),
    
    -- Processing metadata
    processing_time REAL,
    processing_options JSONB DEFAULT '{}',
    error_message TEXT,
    
    -- Engagement metrics
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    downloads_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sketches_user_id ON sketches(user_id);
CREATE INDEX IF NOT EXISTS idx_sketches_status ON sketches(status);
CREATE INDEX IF NOT EXISTS idx_sketches_is_public ON sketches(is_public);
CREATE INDEX IF NOT EXISTS idx_sketches_created_at ON sketches(created_at);
CREATE INDEX IF NOT EXISTS idx_sketches_style ON sketches(style);
CREATE INDEX IF NOT EXISTS idx_sketches_tags ON sketches USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_sketches_public_created ON sketches(is_public, created_at) WHERE is_public = TRUE;

-- Create updated_at trigger
CREATE TRIGGER update_sketches_updated_at BEFORE UPDATE ON sketches 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create likes table
CREATE TABLE IF NOT EXISTS sketch_likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sketch_id UUID NOT NULL REFERENCES sketches(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, sketch_id)
);

CREATE INDEX IF NOT EXISTS idx_sketch_likes_user_id ON sketch_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_sketch_likes_sketch_id ON sketch_likes(sketch_id);

-- Create function to update likes count
CREATE OR REPLACE FUNCTION update_sketch_likes_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE sketches SET likes_count = likes_count + 1 WHERE id = NEW.sketch_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE sketches SET likes_count = likes_count - 1 WHERE id = OLD.sketch_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Create triggers for likes count
CREATE TRIGGER trigger_sketch_likes_insert 
    AFTER INSERT ON sketch_likes 
    FOR EACH ROW EXECUTE FUNCTION update_sketch_likes_count();

CREATE TRIGGER trigger_sketch_likes_delete 
    AFTER DELETE ON sketch_likes 
    FOR EACH ROW EXECUTE FUNCTION update_sketch_likes_count();
"""
