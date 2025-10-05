"""
Database configuration and Supabase client initialization.
"""

from typing import Optional
from supabase import create_client, Client
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manage database connections and operations."""
    
    def __init__(self):
        self._supabase_client: Optional[Client] = None
        self._admin_client: Optional[Client] = None
    
    @property
    def supabase(self) -> Client:
        """Get Supabase client for regular operations."""
        if self._supabase_client is None:
            self._supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Supabase client initialized")
        return self._supabase_client
    
    @property
    def admin_client(self) -> Client:
        """Get Supabase client with service role key for admin operations."""
        if self._admin_client is None:
            if settings.SUPABASE_SERVICE_KEY:
                self._admin_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY
                )
                logger.info("Supabase admin client initialized")
            else:
                logger.warning("No service key provided, using regular client")
                return self.supabase
        return self._admin_client
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            # Test with a simple query
            result = self.supabase.table('users').select('count').execute()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close_connections(self):
        """Close database connections."""
        # Supabase clients don't need explicit closing
        # but we can reset them
        self._supabase_client = None
        self._admin_client = None
        logger.info("Database connections reset")

# Global database manager instance
db_manager = DatabaseManager()

def get_db() -> Client:
    """Dependency to get database client."""
    return db_manager.supabase

def get_admin_db() -> Client:
    """Dependency to get admin database client."""
    return db_manager.admin_client
