import json
from typing import Optional
from uuid import UUID

from auth.schemas import UserResponse
from core.config import settings
from database.models import User

from cache.redis_client import redis_client


async def get_user_from_cache(user_id: UUID) -> Optional[UserResponse]:
    data = await redis_client.get(f"user:{user_id}")
    return UserResponse(**json.loads(data)) if data else None


async def set_user_to_cache(user: User) -> None:
    user_response = UserResponse.model_validate(user)
    await redis_client.setex(
        f"{settings.redis.user_cache_key_prefix}:{user.id}",
        settings.redis.user_cache_ttl,
        user_response.model_dump_json(),
    )
