from auth.dependencies import get_auth_service, get_current_user
from auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from auth.service import AuthService
from cache import event_stream
from cache.dependencies import (
    get_login_event_service,
    get_redis_client,
    get_unique_visitors_service,
    get_user_cache_service,
)
from cache.pubsub import LoginEventService
from cache.unique_visitors import UniqueVisitorsService
from cache.user_cache import UserCacheService
from database.models import User
from database.unit_of_work import UnitOfWork
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis

protected = APIRouter()
public = APIRouter()


@public.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    login_event_service: LoginEventService = Depends(get_login_event_service),
    unique_visitors_service: UniqueVisitorsService = Depends(get_unique_visitors_service),
):
    auth_result = await auth_service.authenticate_user(email=request.email, password=request.password)

    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    await login_event_service.publish_login_event(auth_result["user_id"], request.email)
    await unique_visitors_service.register(auth_result["user_id"])
    return TokenResponse(**auth_result)


@protected.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@public.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    user_cache_service: UserCacheService = Depends(get_user_cache_service),
    redis_client: Redis = Depends(get_redis_client),
):
    async with UnitOfWork() as uow:
        existing_user = await uow.users.get_user_by_email(email=request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )
        user = await uow.users.create_user(request.model_dump())

        await user_cache_service.set_to_cache(user)
        await event_stream.publish_user_registered(redis_client=redis_client, user_id=user.id, email=user.email)
        return UserResponse.model_validate(user)


@protected.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return TokenResponse(**auth_service.refresh_access_token(refresh_token=request.refresh_token))
