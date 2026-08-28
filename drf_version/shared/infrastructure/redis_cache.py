from typing import Any

from shared.domain.interfaces import CacheClient


class RedisCacheClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        value = await self._client.get(key)

        if value is None:
            return None

        return value.decode() if isinstance(value, bytes) else str(value)

    async def set_with_ttl(self, key: str, value: str, ttl: int) -> None:
        await self._client.set(key, value, ex=ttl)
