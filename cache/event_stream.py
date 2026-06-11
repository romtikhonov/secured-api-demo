from uuid import UUID

from core.config import settings
from redis.asyncio import Redis


async def publish_user_registered(redis_client: Redis, user_id: UUID, email: str) -> None:
    await redis_client.xadd(
        settings.redis.user_events_stream,
        {
            "user_id": str(user_id),
            "email": email,
            "event_type": "user_registered",
        },
    )
