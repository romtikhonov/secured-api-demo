from auth.dependencies import require_authentication
from fastapi import APIRouter, Depends

from api.v1.endpoints import auth, user_profiles, users

protected = APIRouter(dependencies=[Depends(require_authentication)])
protected.include_router(auth.protected, prefix="/auth", tags=["auth"])
protected.include_router(user_profiles.protected, prefix="/user-profiles", tags=["user-profiles"])
protected.include_router(users.protected, prefix="/users", tags=["users"])
api_router = APIRouter()
api_router.include_router(auth.public, prefix="/auth", tags=["auth"])
api_router.include_router(protected)
