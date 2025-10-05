"""
Test configuration and fixtures for Sketch It tests.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.config.database import db_manager
from app.services.user_service import UserService
from app.services.sketch_service import SketchService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client for FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def user_service() -> UserService:
    """Create user service instance for testing."""
    return UserService()


@pytest.fixture
def sketch_service() -> SketchService:
    """Create sketch service instance for testing."""
    return SketchService()


@pytest.fixture
async def test_user(user_service: UserService):
    """Create a test user."""
    user = await user_service.create_user(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User"
    )
    yield user
    # Cleanup would go here


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Create sample image bytes for testing."""
    from PIL import Image
    import io
    
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


@pytest.fixture
def auth_headers(test_user):
    """Create authorization headers for authenticated requests."""
    from app.core.security import TokenManager
    
    token = TokenManager.create_access_token(
        data={"sub": test_user.id, "email": test_user.email}
    )
    
    return {"Authorization": f"Bearer {token}"}


# Test database setup
@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Set up test database."""
    # In a real test environment, you would:
    # 1. Create a test database
    # 2. Run migrations
    # 3. Seed with test data
    # 4. Clean up after tests
    
    yield
    
    # Cleanup would go here
