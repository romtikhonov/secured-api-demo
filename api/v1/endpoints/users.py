from datetime import date
from typing import List

from auth.dependencies import get_current_user
from cache.dependencies import get_leaderboard_service, get_unique_visitors_service
from cache.leaderboard import LeaderboardService
from cache.unique_visitors import UniqueVisitorsService
from database.models import User
from fastapi import APIRouter, Depends
from users.schemas import BonusClaimRequest, BonusClaimResponse, LeaderboardEntry, UniqueVisitorsResponse

protected = APIRouter()


@protected.post("/claim-daily-bonus", response_model=BonusClaimResponse)
async def claim_daily_bonus(
    request: BonusClaimRequest,
    current_user: User = Depends(get_current_user),
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
):
    return await leaderboard_service.claim_daily_bonus(current_user.id, request.points)


@protected.get("/leaderboard/top", response_model=List[LeaderboardEntry])
async def get_leaderboard(leaderboard_service: LeaderboardService = Depends(get_leaderboard_service)):
    users = await leaderboard_service.get_top_users(limit=10)
    return [LeaderboardEntry(user_id=id, score=int(score)) for id, score in users]


@protected.get("/analytics/unique-visitors", response_model=UniqueVisitorsResponse)
async def get_daily_unique_visitors(
    unique_visitors_service: UniqueVisitorsService = Depends(get_unique_visitors_service),
):
    return UniqueVisitorsResponse(
        date=date.today().isoformat(), unique_visitors=await unique_visitors_service.get_count()
    )
