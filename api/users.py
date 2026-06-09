from datetime import date
from typing import List

from auth.dependencies import get_current_user
from cache.leaderboard import get_top_users
from cache.unique_visitors import get_unique_visitors_count
from database.models import User
from database.unit_of_work import UnitOfWork
from fastapi import APIRouter, Body, Depends
from users.schemas import LeaderboardEntry
from users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/claim-daily-bonus")
async def claim_daily_bonus(
    points: int = Body(..., gt=0, le=100),
    current_user: User = Depends(get_current_user),
):
    async with UnitOfWork() as uow:
        service = UserService(uow)
        return await service.claim_daily_bonus(current_user.id, points)


@router.get("/leaderboard/top", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    users = await get_top_users(limit=10)
    return [LeaderboardEntry(user_id=id, score=int(score)) for id, score in users]


@router.get("/analytics/unique-visitors")
async def get_daily_unique_visitors():
    count = await get_unique_visitors_count()
    return {"date": date.today().isoformat(), "unique_visitors": count}
