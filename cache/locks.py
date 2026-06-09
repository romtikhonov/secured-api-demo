from uuid import UUID

from redis.asyncio.lock import Lock

from cache.redis_client import redis_client


def create_user_lock(user_id: UUID, operation: str, timeout: int = 10) -> Lock:
    return Lock(redis=redis_client, name=f"lock:{user_id}:{operation}", timeout=timeout, blocking_timeout=10)
