import asyncio
import json

from core.config import settings
from core.logger import logger

from cache.redis_client import redis_client


async def publish_login_event(user_id: str, email: str):
    await redis_client.publish(
        settings.redis.login_channel,
        json.dumps({"user_id": user_id, "email": email, "timestamp": asyncio.get_event_loop().time()}),
    )


async def subscribe_to_logins():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(settings.redis.login_channel)

    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            logger.info(f"Login notification received: {data['email']}")
