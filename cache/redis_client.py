import redis.asyncio as redis
from core.config import settings
from core.secrets import secret_manager

redis_client = redis.Redis(
    host=settings.redis.host,
    port=settings.redis.port,
    password=secret_manager.get_redis_password(),
    decode_responses=True,
    max_connections=20,
    retry_on_timeout=True,
    health_check_interval=30,
)
