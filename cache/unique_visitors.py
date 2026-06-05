from datetime import date
from uuid import UUID

from core.config import settings

from cache.redis_client import redis_client


def get_daily_visitors_key() -> str:
    return f"{settings.redis.visitors_key_prefix}:{date.today().isoformat()}"


async def register_visitor(user_id: UUID) -> None:
    await redis_client.pfadd(get_daily_visitors_key(), str(user_id))


async def get_unique_visitors_count() -> int:
    return await redis_client.pfcount(get_daily_visitors_key())
