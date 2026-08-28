from typing import Optional

import redis.asyncio as aioredis

from app.domain.interfaces import CacheClient


class RedisCacheClient:
    def __init__(self, client: "aioredis.Redis") -> None:
        self._client = client

    async def get(self, key: str) -> Optional[str]:
        value = await self._client.get(key)

        if value is None:
            return None

        if isinstance(value, bytes):
            return value.decode()

        return value

    async def set_with_ttl(self, key: str, value: str, ttl: int) -> None:
        await self._client.set(key, value, ex=ttl)
