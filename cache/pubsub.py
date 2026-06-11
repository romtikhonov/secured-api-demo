import asyncio
import json

from core.config import settings
from core.logger import logger
from redis.asyncio import Redis


class LoginEventService:
    def __init__(self, redis_client: Redis):
        self._redis_client = redis_client

    async def publish_login_event(self, user_id: str, email: str):
        await self._redis_client.publish(
            settings.redis.login_channel,
            json.dumps({"user_id": user_id, "email": email, "timestamp": asyncio.get_event_loop().time()}),
        )

    async def subscribe_to_login_event(self):
        pubsub = self._redis_client.pubsub()
        await pubsub.subscribe(settings.redis.login_channel)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        logger.info(f"Login notification: {data['email']}")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error(f"Invalid login event: {e}")
        except Exception as e:
            logger.error(f"PubSub error: {e}")
        finally:
            await pubsub.close()
