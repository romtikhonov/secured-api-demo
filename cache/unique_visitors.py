from datetime import date
from uuid import UUID

from core.config import settings
from redis.asyncio import Redis


class UniqueVisitorsService:
    def __init__(self, redis_client: Redis):
        self._redis_client = redis_client

    def _get_daily_key(self) -> str:
        return f"{settings.redis.visitors_key_prefix}:{date.today().isoformat()}"

    async def register(self, user_id: UUID) -> None:
        await self._redis_client.pfadd(self._get_daily_key(), str(user_id))

    async def get_count(self) -> int:
        return await self._redis_client.pfcount(self._get_daily_key())
