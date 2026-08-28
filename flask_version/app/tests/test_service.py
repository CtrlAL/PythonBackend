import asyncio
from datetime import datetime, timezone

import pytest

from app.domain.entities import Link
from app.services.url_shortener import LinkNotFoundError, UrlShortenerService


class FakeIdGenerator:
    def __init__(self, start: int = 1) -> None:
        self._n = start

    def generate(self) -> int:
        value = self._n
        self._n += 1

        return value


class FakeRepository:
    def __init__(self) -> None:
        self._store: dict[str, Link] = {}

    async def save(self, link: Link) -> None:
        self._store[link.short_code] = link

    async def get_by_code(self, code: str) -> Link | None:
        return self._store.get(code)

    async def exists(self, code: str) -> bool:
        return code in self._store


class FakeCache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set_with_ttl(self, key: str, value: str, ttl: int) -> None:
        self._store[key] = value


@pytest.fixture
def env() -> tuple[UrlShortenerService, FakeRepository, FakeCache]:
    repository = FakeRepository()
    cache = FakeCache()
    service = UrlShortenerService(
        FakeIdGenerator(),
        repository,
        cache,
    )

    return service, repository, cache


def test_shorten_saves_and_caches(
    env: tuple[UrlShortenerService, FakeRepository, FakeCache],
) -> None:
    service, repository, cache = env

    link = asyncio.run(service.shorten("https://example.com"))

    assert link.short_code
    assert link.long_url == "https://example.com"
    assert cache._store.get(f"short:{link.short_code}") == (
        "https://example.com"
    )
    assert repository._store.get(link.short_code) == link


def test_resolve_returns_cached_without_db(
    env: tuple[UrlShortenerService, FakeRepository, FakeCache],
) -> None:
    service, repository, cache = env

    link = asyncio.run(service.shorten("https://example.com"))

    repository._store.clear()

    resolved = asyncio.run(service.resolve(link.short_code))

    assert resolved == "https://example.com"


def test_resolve_falls_back_to_db_then_caches(
    env: tuple[UrlShortenerService, FakeRepository, FakeCache],
) -> None:
    service, repository, cache = env

    link = asyncio.run(service.shorten("https://example.com"))

    cache_key = f"short:{link.short_code}"
    cache._store.pop(cache_key)

    resolved = asyncio.run(service.resolve(link.short_code))

    assert resolved == "https://example.com"
    assert cache._store.get(cache_key) == "https://example.com"


def test_resolve_raises_when_missing(
    env: tuple[UrlShortenerService, FakeRepository, FakeCache],
) -> None:
    service, _repository, _cache = env

    with pytest.raises(LinkNotFoundError):
        asyncio.run(service.resolve("nope"))
