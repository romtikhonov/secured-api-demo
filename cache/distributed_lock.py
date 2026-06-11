from uuid import uuid4

from redis.asyncio import Redis


class DistributedLock:
    def __init__(self, *, redis_client: Redis, lock_name: str, timeout: int = 10):
        self._lock_name = f"lock:{lock_name}"
        self._timeout = timeout
        self._redis_client = redis_client
        self._lock_value = str(uuid4())

    async def acquire(self) -> bool:
        return (
            await self._redis_client.set(name=self._lock_name, value=self._lock_value, nx=True, ex=self._timeout)
            is True
        )

    async def release(self) -> None:
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        await self._redis_client.eval(lua_script, 1, self._lock_name, self._lock_value)

    async def __aenter__(self):
        if not await self.acquire():
            raise TimeoutError(f"Could not acquire lock '{self._lock_name}'")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()
