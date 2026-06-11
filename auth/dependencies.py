from uuid import UUID

from cache.dependencies import get_user_cache_service
from cache.user_cache import UserCacheService
from core.dependencies import get_secret_provider
from core.logger import logger
from database.unit_of_work import UnitOfWork
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.schemas import UserResponse
from auth.service import AuthService, TokenValidationError

security = HTTPBearer()


def get_auth_service(secret_provider=Depends(get_secret_provider)) -> AuthService:
    return AuthService(secret_provider=secret_provider)


async def get_token_from_header(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
        )
    return credentials.credentials


def require_authentication(
    token: str = Depends(get_token_from_header), auth_service: AuthService = Depends(get_auth_service)
) -> UUID:
    try:
        return auth_service.validate_authentication(token)
    except (TokenValidationError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


async def get_current_user(
    user_id: UUID = Depends(require_authentication),
    user_cache_service: UserCacheService = Depends(get_user_cache_service),
) -> UserResponse:
    cached_user = await user_cache_service.get_from_cache(user_id)
    if cached_user:
        logger.info(f"User {user_id} loaded from CACHE")
        return cached_user

    async with UnitOfWork() as uow:
        user = await uow.users.get_user_by_id(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        logger.info(f"User {user_id} loaded from DATABASE")
        await user_cache_service.set_to_cache(user)
        return UserResponse.model_validate(user)
