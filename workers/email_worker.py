import asyncio
from uuid import uuid4

from cache.dependencies import get_redis_client, init_redis_client
from core.dependencies import get_secret_provider
from core.logger import logger
from redis import ResponseError
from redis.asyncio import Redis

STREAM_NAME = "user_events"
GROUP_NAME = "email_workers"
CONSUMER_NAME = f"worker-{str(uuid4())}"


async def create_consumer_group(redis_client: Redis):
    redis_client = get_redis_client()
    try:
        await redis_client.xgroup_create(STREAM_NAME, GROUP_NAME, mkstream=True)
        logger.info(f"Consumer group '{GROUP_NAME}' created")
    except ResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.info(f"Consumer group '{GROUP_NAME}' already exists")
        else:
            raise


async def process_events():
    secret_provider = get_secret_provider()
    init_redis_client(secret_provider.get_redis_password())
    redis_client = get_redis_client()
    await create_consumer_group(redis_client=redis_client)
    logger.info(f"Worker '{CONSUMER_NAME}' started listening for events...")

    while True:
        try:
            events = await redis_client.xreadgroup(GROUP_NAME, CONSUMER_NAME, {STREAM_NAME: ">"}, count=1, block=5000)

            if not events:
                logger.debug("No events received (timeout)")
                continue

            for stream, event_list in events:
                for event_id, event_data in event_list:
                    logger.info(f"Processing event: {event_data}")
                    await redis_client.xack(STREAM_NAME, GROUP_NAME, event_id)

        except Exception as e:
            logger.error(f"Error processing events: {e}")


if __name__ == "__main__":
    asyncio.run(process_events())
