from uuid import UUID

from cache.user_cache import get_user_from_cache, set_user_to_cache
from core.logger import logger
from database.unit_of_work import UnitOfWork
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.schemas import UserResponse
from auth.utils import TokenValidationError, verify_token

security = HTTPBearer()


async def get_token_from_header(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
        )
    return credentials.credentials


def validate_access_token(token: str) -> UUID:
    try:
        payload = verify_token(token)
        if payload.get("token_type") != "access":
            raise TokenValidationError("Invalid token type")
        user_id = payload.get("sub", None)
        if not user_id:
            raise TokenValidationError("User ID not found in token")
        return UUID(user_id)
    except (TokenValidationError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


async def get_current_user(token: str = Depends(get_token_from_header)) -> UserResponse:
    user_id = validate_access_token(token)

    cached_user = await get_user_from_cache(user_id)
    if cached_user:
        logger.info(f"✅ User {user_id} loaded from CACHE")
        return cached_user

    async with UnitOfWork() as uow:
        user = await uow.users.get_user_by_id(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        logger.info(f"💾 User {user_id} loaded from DATABASE")
        await set_user_to_cache(user)
        return UserResponse.model_validate(user)
