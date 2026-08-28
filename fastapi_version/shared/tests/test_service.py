# shared/tests/test_service.py
import asyncio

import pytest

from shared.domain.codecs import encode
from shared.domain.entities import Link
from shared.domain.interfaces import CacheClient, IdGenerator, LinkRepository
from shared.services.url_shortener import LinkNotFoundError, UrlShortenerService


class FakeIdGenerator(IdGenerator):
    def __init__(self, start: int = 1) -> None:
        self._n = start

    def generate(self) -> int:
        value = self._n
        self._n += 1

        return value


class FakeRepository(LinkRepository):
    def __init__(self) -> None:
        self._store: dict[str, Link] = {}

    async def save(self, link: Link) -> None:
        self._store[link.short_code] = link

    async def get_by_code(self, code: str) -> Link | None:
        return self._store.get(code)

    async def exists(self, code: str) -> bool:
        return code in self._store


class FakeCache(CacheClient):
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set_with_ttl(self, key: str, value: str, ttl: int) -> None:
        self._store[key] = value


def _make_service() -> UrlShortenerService:
    return UrlShortenerService(
        id_generator=FakeIdGenerator(42),
        repository=FakeRepository(),
        cache=FakeCache(),
        ttl=3600,
    )


def test_shorten_saves_and_caches() -> None:
    service = _make_service()
    link = asyncio.run(service.shorten("https://example.com"))

    assert link.short_code == encode(42)
    assert link.long_url == "https://example.com"


def test_resolve_uses_cache() -> None:
    service = _make_service()
    asyncio.run(service.shorten("https://example.com"))
    url = asyncio.run(service.resolve(encode(42)))

    assert url == "https://example.com"


def test_resolve_missing_raises() -> None:
    service = _make_service()

    with pytest.raises(LinkNotFoundError):
        asyncio.run(service.resolve("missing"))
