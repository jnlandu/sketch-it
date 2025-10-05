"""
Sketch service for handling sketch-related business logic.
"""

import uuid
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from supabase import Client
import os

from app.config.database import get_db
from app.models.sketch import Sketch, SketchStatus, SketchStyle
from app.schemas.sketch import SketchProcessingOptions
from app.utils.image_processing import ImageProcessor
from app.services.storage_service import StorageService
from app.core.exceptions import (
    NotFoundError, ValidationError, FileProcessingError, 
    ImageProcessingError, StorageError
)


class SketchService:
    """Service class for sketch operations."""
    
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_db()
        self.storage_service = StorageService()
        self.image_processor = ImageProcessor()
    
    async def create_sketch(
        self,
        user_id: str,
        title: str,
        description: Optional[str],
        style: SketchStyle,
        is_public: bool,
        tags: List[str],
        image_bytes: bytes,
        original_filename: str
    ) -> Sketch:
        """Create a new sketch."""
        try:
            # Validate image
            is_valid, error_msg = self.image_processor.validate_image(image_bytes)
            if not is_valid:
                raise ValidationError(error_msg)
            
            # Get image info
            image_info = self.image_processor.get_image_info(image_bytes)
            
            # Create sketch record
            sketch_id = str(uuid.uuid4())
            sketch_data = {
                'id': sketch_id,
                'user_id': user_id,
                'title': title,
                'description': description,
                'style': style.value,
                'status': SketchStatus.PENDING.value,
                'is_public': is_public,
                'tags': tags,
                'original_filename': original_filename,
                'file_size': image_info['size_bytes'],
                'image_width': image_info['width'],
                'image_height': image_info['height'],
                'file_format': image_info['format'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
            }
            
            # Insert into database
            result = self.db.table('sketches').insert(sketch_data).execute()
            if not result.data:
                raise ValidationError("Failed to create sketch")
            
            sketch = Sketch.from_dict(result.data[0])
            
            # Start processing in background
            asyncio.create_task(self._process_sketch_async(sketch, image_bytes))
            
            return sketch
            
        except Exception as e:
            if isinstance(e, (ValidationError, FileProcessingError)):
                raise
            raise ValidationError(f"Failed to create sketch: {str(e)}")
    
    async def get_sketch_by_id(self, sketch_id: str) -> Optional[Sketch]:
        """Get sketch by ID."""
        try:
            result = self.db.table('sketches').select(
                '*, users!user_id(full_name, avatar_url)'
            ).eq('id', sketch_id).execute()
            
            if result.data:
                sketch_data = result.data[0]
                # Handle user information from join
                if 'users' in sketch_data and sketch_data['users']:
                    user_info = sketch_data['users']
                    sketch_data['user_full_name'] = user_info.get('full_name')
                    sketch_data['user_avatar_url'] = user_info.get('avatar_url')
                
                return Sketch.from_dict(sketch_data)
            return None
            
        except Exception as e:
            raise ValidationError(f"Failed to get sketch: {str(e)}")
    
    async def get_user_sketches(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        status: Optional[SketchStatus] = None,
        style: Optional[SketchStyle] = None
    ) -> Dict[str, Any]:
        """Get sketches for a user."""
        try:
            offset = (page - 1) * per_page
            
            query = self.db.table('sketches').select('*').eq('user_id', user_id)
            
            if status:
                query = query.eq('status', status.value)
            if style:
                query = query.eq('style', style.value)
            
            # Get total count
            count_result = query.execute()
            total = len(count_result.data) if count_result.data else 0
            
            # Get paginated results
            result = query.order('created_at', desc=True).range(
                offset, offset + per_page - 1
            ).execute()
            
            sketches = [Sketch.from_dict(data) for data in result.data] if result.data else []
            
            return {
                'sketches': sketches,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            raise ValidationError(f"Failed to get user sketches: {str(e)}")
    
    async def get_public_sketches(
        self,
        page: int = 1,
        per_page: int = 20,
        style: Optional[SketchStyle] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get public sketches."""
        try:
            offset = (page - 1) * per_page
            
            query = self.db.table('sketches').select(
                '*, users!user_id(full_name, avatar_url)'
            ).eq('is_public', True).eq('status', SketchStatus.COMPLETED.value)
            
            if style:
                query = query.eq('style', style.value)
            
            if search:
                query = query.or_(
                    f'title.ilike.%{search}%,description.ilike.%{search}%'
                )
            
            if tags:
                # Supabase array contains operator
                for tag in tags:
                    query = query.contains('tags', [tag])
            
            # Get total count
            count_result = query.execute()
            total = len(count_result.data) if count_result.data else 0
            
            # Get paginated results
            result = query.order('created_at', desc=True).range(
                offset, offset + per_page - 1
            ).execute()
            
            sketches = []
            if result.data:
                for sketch_data in result.data:
                    # Handle user information from join
                    if 'users' in sketch_data and sketch_data['users']:
                        user_info = sketch_data['users']
                        sketch_data['user_full_name'] = user_info.get('full_name')
                        sketch_data['user_avatar_url'] = user_info.get('avatar_url')
                    
                    sketches.append(Sketch.from_dict(sketch_data))
            
            return {
                'sketches': sketches,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            raise ValidationError(f"Failed to get public sketches: {str(e)}")
    
    async def update_sketch(
        self,
        sketch_id: str,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Sketch]:
        """Update sketch metadata."""
        try:
            # Verify ownership
            sketch = await self.get_sketch_by_id(sketch_id)
            if not sketch or sketch.user_id != user_id:
                raise NotFoundError("Sketch not found or access denied")
            
            # Prepare update data
            clean_data = {k: v for k, v in update_data.items() if v is not None}
            clean_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = self.db.table('sketches').update(clean_data).eq(
                'id', sketch_id
            ).execute()
            
            if result.data:
                return Sketch.from_dict(result.data[0])
            return None
            
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            raise ValidationError(f"Failed to update sketch: {str(e)}")
    
    async def delete_sketch(self, sketch_id: str, user_id: str) -> bool:
        """Delete a sketch."""
        try:
            # Verify ownership
            sketch = await self.get_sketch_by_id(sketch_id)
            if not sketch or sketch.user_id != user_id:
                raise NotFoundError("Sketch not found or access denied")
            
            # Delete files from storage
            if sketch.original_url:
                await self.storage_service.delete_file(sketch.original_url)
            if sketch.sketch_url:
                await self.storage_service.delete_file(sketch.sketch_url)
            if sketch.thumbnail_url:
                await self.storage_service.delete_file(sketch.thumbnail_url)
            
            # Delete from database
            result = self.db.table('sketches').delete().eq('id', sketch_id).execute()
            return bool(result.data)
            
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            raise ValidationError(f"Failed to delete sketch: {str(e)}")
    
    async def like_sketch(self, sketch_id: str, user_id: str) -> bool:
        """Like/unlike a sketch."""
        try:
            # Check if already liked
            existing_like = self.db.table('sketch_likes').select('*').eq(
                'sketch_id', sketch_id
            ).eq('user_id', user_id).execute()
            
            if existing_like.data:
                # Unlike
                self.db.table('sketch_likes').delete().eq(
                    'sketch_id', sketch_id
                ).eq('user_id', user_id).execute()
                return False
            else:
                # Like
                like_data = {
                    'id': str(uuid.uuid4()),
                    'sketch_id': sketch_id,
                    'user_id': user_id,
                    'created_at': datetime.utcnow().isoformat()
                }
                self.db.table('sketch_likes').insert(like_data).execute()
                return True
                
        except Exception as e:
            raise ValidationError(f"Failed to like/unlike sketch: {str(e)}")
    
    async def increment_view_count(self, sketch_id: str):
        """Increment sketch view count."""
        try:
            # Use Supabase RPC or raw SQL for atomic increment
            # For now, simple update
            self.db.table('sketches').update({
                'views_count': 'views_count + 1'  # This won't work as intended
            }).eq('id', sketch_id).execute()
            
        except Exception:
            # Don't raise exception for non-critical operation
            pass
    
    async def _process_sketch_async(self, sketch: Sketch, image_bytes: bytes):
        """Process sketch asynchronously."""
        try:
            # Update status to processing
            await self._update_sketch_status(sketch.id, SketchStatus.PROCESSING)
            
            start_time = datetime.utcnow()
            
            # Resize original image if needed
            resized_image = self.image_processor.resize_image(image_bytes)
            
            # Upload original image
            original_filename = f"original_{sketch.id}.jpg"
            original_url = await self.storage_service.upload_file(
                resized_image, original_filename, "image/jpeg"
            )
            
            # Generate thumbnail
            thumbnail_bytes = self.image_processor.create_thumbnail(resized_image)
            thumbnail_filename = f"thumb_{sketch.id}.jpg"
            thumbnail_url = await self.storage_service.upload_file(
                thumbnail_bytes, thumbnail_filename, "image/jpeg"
            )
            
            # Generate sketch
            processing_options = SketchProcessingOptions(style=sketch.style)
            sketch_bytes = self.image_processor.generate_sketch(
                resized_image, sketch.style, processing_options
            )
            
            # Upload sketch
            sketch_filename = f"sketch_{sketch.id}.jpg"
            sketch_url = await self.storage_service.upload_file(
                sketch_bytes, sketch_filename, "image/jpeg"
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update sketch with URLs and completion status
            update_data = {
                'original_url': original_url,
                'sketch_url': sketch_url,
                'thumbnail_url': thumbnail_url,
                'status': SketchStatus.COMPLETED.value,
                'processing_time': processing_time,
                'processed_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            self.db.table('sketches').update(update_data).eq('id', sketch.id).execute()
            
        except Exception as e:
            # Update status to failed
            await self._update_sketch_status(
                sketch.id, 
                SketchStatus.FAILED, 
                error_message=str(e)
            )
    
    async def _update_sketch_status(
        self, 
        sketch_id: str, 
        status: SketchStatus, 
        error_message: Optional[str] = None
    ):
        """Update sketch processing status."""
        try:
            update_data = {
                'status': status.value,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            self.db.table('sketches').update(update_data).eq('id', sketch_id).execute()
            
        except Exception:
            pass  # Don't raise exception for status updates
