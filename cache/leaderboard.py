from uuid import UUID

from core.config import settings

from cache.redis_client import redis_client


async def update_user_score(user_id: UUID, points: int) -> int:
    new_score = await redis_client.zincrby(settings.redis.leaderboard_key, points, str(user_id))
    return int(new_score)


async def get_top_users(limit: int = settings.redis.leaderboard_top_n):
    return await redis_client.zrevrange(settings.redis.leaderboard_key, 0, limit - 1, withscores=True)


async def get_user_rank(user_id: UUID) -> int | None:
    rank = await redis_client.zrevrank(settings.redis.leaderboard_key, str(user_id))
    return rank + 1 if rank is not None else None
