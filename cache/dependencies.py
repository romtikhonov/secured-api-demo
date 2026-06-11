from typing import Optional

from core.config import settings
from fastapi import Depends
from redis.asyncio import Redis

from cache.leaderboard import LeaderboardService
from cache.pubsub import LoginEventService
from cache.unique_visitors import UniqueVisitorsService
from cache.user_cache import UserCacheService

_redis_client: Optional[Redis] = None


def init_redis_client(redis_password: str):
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            password=redis_password,
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
            health_check_interval=30,
        )


def get_redis_client() -> Redis:
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis_client() first.")
    return _redis_client


def get_leaderboard_service(redis: Redis = Depends(get_redis_client)) -> LeaderboardService:
    return LeaderboardService(redis)


def get_login_event_service(redis: Redis = Depends(get_redis_client)) -> LoginEventService:
    return LoginEventService(redis)


def get_unique_visitors_service(redis: Redis = Depends(get_redis_client)) -> UniqueVisitorsService:
    return UniqueVisitorsService(redis)


def get_user_cache_service(redis: Redis = Depends(get_redis_client)) -> UserCacheService:
    return UserCacheService(redis)
