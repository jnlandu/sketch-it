"""
Main API router that includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.sketches import router as sketches_router
from app.api.v1.subscriptions import router as subscriptions_router

# Create main API router
api_router = APIRouter()

# Include all routers with their prefixes
api_router.include_router(
    auth_router,
    prefix="/v1/auth",
    tags=["authentication"]
)

api_router.include_router(
    users_router,
    prefix="/v1/users",
    tags=["users"]
)

api_router.include_router(
    sketches_router,
    prefix="/v1/sketches",
    tags=["sketches"]
)

api_router.include_router(
    subscriptions_router,
    prefix="/v1/subscriptions",
    tags=["subscriptions"]
)
