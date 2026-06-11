import json
from typing import Optional
from uuid import UUID

from auth.schemas import UserResponse
from core.config import settings
from core.logger import logger
from database.models import User
from redis.asyncio import Redis


class UserCacheService:
    def __init__(self, redis_client: Redis):
        self._redis_client = redis_client

    async def get_from_cache(self, user_id: UUID) -> Optional[UserResponse]:
        try:
            data = await self._redis_client.get(f"{settings.redis.user_cache_key_prefix}:{user_id}")
            return UserResponse(**json.loads(data)) if data else None
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Cache deserialization error for user {user_id}: {e}")
            return None

    async def set_to_cache(self, user: User) -> None:
        user_response = UserResponse.model_validate(user)
        await self._redis_client.setex(
            f"{settings.redis.user_cache_key_prefix}:{user.id}",
            settings.redis.user_cache_ttl,
            user_response.model_dump_json(),
        )
