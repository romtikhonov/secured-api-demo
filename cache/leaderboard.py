from datetime import date
from uuid import UUID

from core.config import settings
from database.unit_of_work import UnitOfWork
from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.asyncio.lock import Lock
from users.service import UserService


class LeaderboardService:
    def __init__(self, redis_client: Redis):
        self._redis_client = redis_client

    def _create_user_lock(self, user_id: UUID, operation: str, timeout: int = 10) -> Lock:
        return Lock(redis=self._redis_client, name=f"lock:{user_id}:{operation}", timeout=timeout, blocking_timeout=10)

    async def set_user_score(self, user_id: UUID, total_score: int) -> None:
        await self._redis_client.zadd(settings.redis.leaderboard_key, {str(user_id): total_score})

    async def get_top_users(self, limit: int = settings.redis.leaderboard_top_n):
        return await self._redis_client.zrevrange(settings.redis.leaderboard_key, 0, limit - 1, withscores=True)

    async def get_user_rank(self, user_id: UUID) -> int | None:
        rank = await self._redis_client.zrevrank(settings.redis.leaderboard_key, str(user_id))
        return rank + 1 if rank is not None else None

    async def claim_daily_bonus(self, user_id: UUID, bonus_points: int) -> dict:
        lock = self._create_user_lock(user_id=user_id, operation=f"claim_daily_bonus:{date.today().isoformat()}")
        if not await lock.acquire():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

        try:
            claimed_key = f"bonus_claimed:{user_id}:{date.today().isoformat()}"
            if await self._redis_client.exists(claimed_key):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bonus already claimed")

            async with UnitOfWork() as uow:
                user_service = UserService(uow)
                new_score = await user_service.add_points(user_id=user_id, points=bonus_points)

                # Update leaderboard sync (Write-Through)
                await self.set_user_score(user_id, new_score)
                await self._redis_client.setex(name=claimed_key, time=86400, value="1")

            return {"new_score": new_score}
        finally:
            await lock.release()
