#!/usr/bin/env python3
"""
Database initialization script for Sketch It.
Creates tables and sets up initial database schema.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app.config.database import db_manager
from app.models.user import USER_TABLE_SCHEMA
from app.models.sketch import SKETCH_TABLE_SCHEMA
from app.models.subscription import SUBSCRIPTION_TABLE_SCHEMA


async def create_tables():
    """Create all database tables."""
    try:
        print("🔄 Initializing database...")
        
        # Test connection
        if not db_manager.test_connection():
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connection successful")
        
        # Get admin client for schema operations
        admin_db = db_manager.admin_client
        
        # Create tables using raw SQL
        print("🔄 Creating users table...")
        admin_db.rpc('exec_sql', {'sql': USER_TABLE_SCHEMA}).execute()
        print("✅ Users table created")
        
        print("🔄 Creating sketches table...")
        admin_db.rpc('exec_sql', {'sql': SKETCH_TABLE_SCHEMA}).execute()
        print("✅ Sketches table created")
        
        print("🔄 Creating subscriptions table...")
        admin_db.rpc('exec_sql', {'sql': SUBSCRIPTION_TABLE_SCHEMA}).execute()
        print("✅ Subscriptions table created")
        
        print("🎉 Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False


async def create_storage_buckets():
    """Create storage buckets in Supabase."""
    try:
        print("🔄 Creating storage buckets...")
        
        admin_db = db_manager.admin_client
        
        # Create main storage bucket
        bucket_config = {
            'id': 'sketch-storage',
            'name': 'sketch-storage',
            'public': True,
            'file_size_limit': 10485760,  # 10MB
            'allowed_mime_types': ['image/jpeg', 'image/png', 'image/webp']
        }
        
        try:
            admin_db.storage.create_bucket(bucket_config['id'], bucket_config)
            print("✅ Storage bucket created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️ Storage bucket already exists")
            else:
                print(f"⚠️ Storage bucket creation failed: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage bucket creation failed: {str(e)}")
        return False


async def create_rls_policies():
    """Create Row Level Security policies."""
    try:
        print("🔄 Creating RLS policies...")
        
        admin_db = db_manager.admin_client
        
        # Enable RLS on tables
        rls_commands = [
            "ALTER TABLE users ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE sketches ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE sketch_likes ENABLE ROW LEVEL SECURITY;",
            
            # Users policies
            """
            CREATE POLICY "Users can view own profile" ON users
            FOR SELECT USING (auth.uid()::text = id);
            """,
            
            """
            CREATE POLICY "Users can update own profile" ON users
            FOR UPDATE USING (auth.uid()::text = id);
            """,
            
            # Sketches policies
            """
            CREATE POLICY "Users can view own sketches" ON sketches
            FOR SELECT USING (auth.uid()::text = user_id);
            """,
            
            """
            CREATE POLICY "Anyone can view public sketches" ON sketches
            FOR SELECT USING (is_public = true AND status = 'completed');
            """,
            
            """
            CREATE POLICY "Users can insert own sketches" ON sketches
            FOR INSERT WITH CHECK (auth.uid()::text = user_id);
            """,
            
            """
            CREATE POLICY "Users can update own sketches" ON sketches
            FOR UPDATE USING (auth.uid()::text = user_id);
            """,
            
            """
            CREATE POLICY "Users can delete own sketches" ON sketches
            FOR DELETE USING (auth.uid()::text = user_id);
            """,
            
            # Subscriptions policies
            """
            CREATE POLICY "Users can view own subscription" ON subscriptions
            FOR SELECT USING (auth.uid()::text = user_id);
            """,
            
            # Sketch likes policies
            """
            CREATE POLICY "Users can manage own likes" ON sketch_likes
            FOR ALL USING (auth.uid()::text = user_id);
            """,
            
            """
            CREATE POLICY "Anyone can view likes for public sketches" ON sketch_likes
            FOR SELECT USING (
                EXISTS (
                    SELECT 1 FROM sketches 
                    WHERE sketches.id = sketch_likes.sketch_id 
                    AND sketches.is_public = true
                )
            );
            """
        ]
        
        for command in rls_commands:
            try:
                admin_db.rpc('exec_sql', {'sql': command}).execute()
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"⚠️ RLS policy command failed: {str(e)}")
        
        print("✅ RLS policies created")
        return True
        
    except Exception as e:
        print(f"❌ RLS policies creation failed: {str(e)}")
        return False


async def create_functions():
    """Create database functions."""
    try:
        print("🔄 Creating database functions...")
        
        admin_db = db_manager.admin_client
        
        # Function to execute SQL (if not exists)
        exec_sql_function = """
        CREATE OR REPLACE FUNCTION exec_sql(sql text)
        RETURNS void AS $$
        BEGIN
            EXECUTE sql;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
        
        admin_db.rpc('exec_sql', {'sql': exec_sql_function}).execute()
        print("✅ Database functions created")
        return True
        
    except Exception as e:
        print(f"❌ Function creation failed: {str(e)}")
        return False


async def main():
    """Main initialization function."""
    print("🚀 Starting Sketch It database initialization...")
    
    # Check environment variables
    required_env_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file with the required variables.")
        return False
    
    success = True
    
    # Create functions first
    success = await create_functions() and success
    
    # Create tables
    success = await create_tables() and success
    
    # Create storage buckets
    success = await create_storage_buckets() and success
    
    # Create RLS policies
    success = await create_rls_policies() and success
    
    if success:
        print("\n🎉 Database initialization completed successfully!")
        print("You can now start the application.")
    else:
        print("\n❌ Database initialization completed with errors.")
        print("Please check the logs and try again.")
    
    return success


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run initialization
    asyncio.run(main())
