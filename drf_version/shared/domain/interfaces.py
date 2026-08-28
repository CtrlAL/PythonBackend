from typing import Protocol, runtime_checkable

from shared.domain.entities import Link


@runtime_checkable
class IdGenerator(Protocol):
    def generate(self) -> int: ...


@runtime_checkable
class LinkRepository(Protocol):
    async def save(self, link: Link) -> None: ...

    async def get_by_code(self, code: str) -> Link | None: ...

    async def exists(self, code: str) -> bool: ...


@runtime_checkable
class CacheClient(Protocol):
    async def get(self, key: str) -> str | None: ...

    async def set_with_ttl(self, key: str, value: str, ttl: int) -> None: ...
