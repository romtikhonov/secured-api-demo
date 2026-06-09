from datetime import date

from auth.dependencies import get_current_user
from auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from auth.service import AuthService
from cache.event_stream import publish_user_registered
from cache.leaderboard import get_top_players, get_user_rank
from cache.pubsub import publish_login_event
from cache.unique_visitors import get_unique_visitors_count, register_visitor
from cache.user_cache import set_user_to_cache
from database.models import User
from database.unit_of_work import UnitOfWork
from fastapi import APIRouter, Body, Depends, HTTPException, status
from users.service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    auth_result = await AuthService.authenticate_user(email=request.email, password=request.password)

    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    await publish_login_event(str(auth_result["user_id"]), request.email)

    return TokenResponse(**auth_result)


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(get_current_user)):
    await register_visitor(current_user.id)
    return current_user


@router.post("/register", response_model=UserResponse)
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


@router.post("/leaderboard/add-points")
async def add_points(
    points: int = Body(..., gt=0),
    current_user: User = Depends(get_current_user),
):
    async with UnitOfWork() as uow:
        service = UserService(uow)
        new_score = await service.add_points(current_user.id, points)
        rank = await get_user_rank(current_user.id)
        return {"total_score": new_score, "current_rank": rank}


@router.get("/leaderboard/top")
async def get_leaderboard():
    return [{"user_id": player_id, "score": int(score)} for player_id, score in await get_top_players(limit=10)]


@router.get("/analytics/unique-visitors")
async def get_daily_unique_visitors():
    count = await get_unique_visitors_count()
    return {"date": date.today().isoformat(), "unique_visitors": count}
