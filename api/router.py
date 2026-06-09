from fastapi import APIRouter

from .auth import router as auth_router
from .user_profiles import router as user_profiles_router
from .users import router as user_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(user_profiles_router)
api_router.include_router(user_router)
