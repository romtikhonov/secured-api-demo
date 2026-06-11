from core.config import settings
from core.dependencies import get_secret_provider
from fastapi import Depends
from redis.asyncio import Redis

from cache.leaderboard import LeaderboardService
from cache.pubsub import LoginEventService
from cache.unique_visitors import UniqueVisitorsService
from cache.user_cache import UserCacheService

redis_client = Redis(
    host=settings.redis.host,
    port=settings.redis.port,
    password=get_secret_provider().get_redis_password(),
    decode_responses=True,
    max_connections=20,
    retry_on_timeout=True,
    health_check_interval=30,
)


def get_redis_client() -> Redis:
    return redis_client


def get_leaderboard_service(redis: Redis = Depends(get_redis_client)) -> LeaderboardService:
    return LeaderboardService(redis)


def get_login_event_service(redis: Redis = Depends(get_redis_client)) -> LoginEventService:
    return LoginEventService(redis)


def get_unique_visitors_service(redis: Redis = Depends(get_redis_client)) -> UniqueVisitorsService:
    return UniqueVisitorsService(redis)


def get_user_cache_service(redis: Redis = Depends(get_redis_client)) -> UserCacheService:
    return UserCacheService(redis)
