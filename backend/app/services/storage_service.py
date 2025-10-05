"""
Storage service for handling file uploads and management with Supabase Storage.
"""

import os
from typing import Optional
from supabase import Client
import uuid
from datetime import datetime, timedelta

from app.config.database import get_db
from app.config.settings import settings
from app.core.exceptions import StorageError
from app.utils.helpers import generate_filename, calculate_file_hash


class StorageService:
    """Service class for file storage operations."""
    
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_db()
        self.bucket_name = settings.STORAGE_BUCKET
    
    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        folder: str = "sketches"
    ) -> str:
        """Upload file to Supabase Storage."""
        try:
            # Generate unique filename
            unique_filename = generate_filename(filename, folder)
            file_path = f"{folder}/{unique_filename}"
            
            # Upload to Supabase Storage
            result = self.db.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_bytes,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600"  # 1 hour cache
                }
            )
            
            if result.get('error'):
                raise StorageError(f"Upload failed: {result['error']}")
            
            # Get public URL
            public_url = self.db.storage.from_(self.bucket_name).get_public_url(file_path)
            
            return public_url
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to upload file: {str(e)}")
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file from storage."""
        try:
            # Extract file path from URL
            file_path = self._extract_path_from_url(file_url)
            if not file_path:
                return False
            
            # Delete from Supabase Storage
            result = self.db.storage.from_(self.bucket_name).remove([file_path])
            
            return not bool(result.get('error'))
            
        except Exception as e:
            # Don't raise exception for delete operations
            return False
    
    async def get_signed_url(
        self,
        file_path: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """Get signed URL for private file access."""
        try:
            result = self.db.storage.from_(self.bucket_name).create_signed_url(
                path=file_path,
                expires_in=expires_in
            )
            
            if result.get('error'):
                return None
            
            return result.get('signedURL')
            
        except Exception:
            return None
    
    async def upload_user_avatar(
        self,
        user_id: str,
        file_bytes: bytes,
        content_type: str
    ) -> str:
        """Upload user avatar."""
        try:
            # Generate avatar filename
            extension = "jpg" if "jpeg" in content_type else content_type.split("/")[-1]
            filename = f"avatar_{user_id}.{extension}"
            
            return await self.upload_file(
                file_bytes=file_bytes,
                filename=filename,
                content_type=content_type,
                folder="avatars"
            )
            
        except Exception as e:
            raise StorageError(f"Failed to upload avatar: {str(e)}")
    
    async def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get file information from storage."""
        try:
            # This would require additional Supabase storage API calls
            # For now, return basic info
            return {
                'path': file_path,
                'exists': True  # Would need actual check
            }
            
        except Exception:
            return None
    
    def _extract_path_from_url(self, file_url: str) -> Optional[str]:
        """Extract file path from public URL."""
        try:
            # Parse Supabase storage URL to get file path
            # Format: https://project.supabase.co/storage/v1/object/public/bucket/path
            parts = file_url.split(f"/storage/v1/object/public/{self.bucket_name}/")
            if len(parts) == 2:
                return parts[1]
            return None
            
        except Exception:
            return None
    
    async def create_upload_token(
        self,
        user_id: str,
        filename: str,
        file_size: int
    ) -> dict:
        """Create upload token for direct file uploads."""
        try:
            # Generate upload token
            upload_token = str(uuid.uuid4())
            
            # Store upload metadata (in a real implementation, use database)
            upload_data = {
                'token': upload_token,
                'user_id': user_id,
                'filename': filename,
                'file_size': file_size,
                'expires_at': datetime.utcnow() + timedelta(hours=1),
                'used': False
            }
            
            # In production, store this in database
            # For now, return the token
            return {
                'upload_token': upload_token,
                'expires_at': upload_data['expires_at'].isoformat(),
                'max_file_size': settings.MAX_FILE_SIZE
            }
            
        except Exception as e:
            raise StorageError(f"Failed to create upload token: {str(e)}")
    
    async def verify_upload_token(self, token: str, user_id: str) -> bool:
        """Verify upload token."""
        try:
            # In production, check token in database
            # For now, basic validation
            return len(token) == 36  # UUID length
            
        except Exception:
            return False
    
    async def get_storage_usage(self, user_id: str) -> dict:
        """Get storage usage for user."""
        try:
            # This would require aggregating file sizes from database
            # For now, return placeholder
            return {
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_formatted': '0 B',
                'limit_bytes': settings.MAX_FILE_SIZE * 100,  # 100 files limit
                'usage_percentage': 0
            }
            
        except Exception as e:
            raise StorageError(f"Failed to get storage usage: {str(e)}")
    
    async def cleanup_old_files(self, days_old: int = 30):
        """Cleanup old temporary files."""
        try:
            # This would be implemented as a background task
            # to clean up failed uploads, temporary files, etc.
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Implementation would scan storage and remove old files
            # that are no longer referenced in the database
            
            return True
            
        except Exception as e:
            # Don't raise exception for cleanup operations
            return False
