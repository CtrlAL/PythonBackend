# shared/infrastructure/redis_cache.py
import os

from redis.asyncio import Redis

from shared.domain.interfaces import CacheClient


class RedisCacheClient(CacheClient):
    def __init__(self, url: str | None = None) -> None:
        self._url = url or os.environ.get(
            "REDIS_URL", "redis://127.0.0.1:6379/0"
        )
        self._redis: Redis = Redis.from_url(self._url)

    async def get(self, key: str) -> str | None:
        value = await self._redis.get(key)

        if value is None:
            return None

        return value.decode()

    async def set_with_ttl(self, key: str, value: str, ttl: int) -> None:
        await self._redis.set(key, value, ex=ttl)
