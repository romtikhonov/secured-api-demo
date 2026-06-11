from auth.dependencies import get_current_user
from auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from auth.service import AuthService
from cache.event_stream import publish_user_registered
from cache.pubsub import publish_login_event
from cache.unique_visitors import register_visitor
from cache.user_cache import set_user_to_cache
from database.models import User
from database.unit_of_work import UnitOfWork
from fastapi import APIRouter, Depends, HTTPException, status

protected = APIRouter()
public = APIRouter()


@public.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    auth_result = await AuthService.authenticate_user(email=request.email, password=request.password)

    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    await publish_login_event(auth_result["user_id"], request.email)
    await register_visitor(auth_result["user_id"])
    return TokenResponse(**auth_result)


@protected.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@public.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    async with UnitOfWork() as uow:
        existing_user = await uow.users.get_user_by_email(email=request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )
        user = await uow.users.create_user(request.model_dump())

        await set_user_to_cache(user)
        await publish_user_registered(user_id=user.id, email=user.email)
        return UserResponse.model_validate(user)


@protected.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(request: RefreshRequest):
    refresh_result = AuthService.refresh_access_token(refresh_token=request.refresh_token)
    return TokenResponse(**refresh_result)
