import asyncio
from datetime import datetime, timezone

from shared.domain.codecs import decode, encode
from shared.domain.entities import Link
from shared.services.url_shortener import (
    LinkNotFoundError,
    UrlShortenerService,
)


class FakeIdGenerator:
    def __init__(self) -> None:
        self._counter = 0

    def generate(self) -> int:
        self._counter += 1

        return self._counter


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


def _make_service() -> tuple[UrlShortenerService, FakeCache, FakeRepository]:
    cache = FakeCache()
    repository = FakeRepository()

    service = UrlShortenerService(
        id_generator=FakeIdGenerator(),
        repository=repository,
        cache=cache,
        ttl=3600,
    )

    return service, cache, repository


def test_shorten_saves_and_caches() -> None:
    service, cache, repo = _make_service()

    link = asyncio.run(service.shorten("https://example.com"))

    assert link.short_code == encode(1)
    assert link.long_url == "https://example.com"
    assert link.created_at.tzinfo is not None
    assert repo._store[link.short_code] is link
    assert cache._store[f"short:{link.short_code}"] == "https://example.com"


def test_resolve_uses_cache() -> None:
    service, cache, repo = _make_service()

    link = asyncio.run(service.shorten("https://example.com"))
    cache._store.clear()

    resolved = asyncio.run(service.resolve(link.short_code))

    assert resolved == "https://example.com"
    assert cache._store[f"short:{link.short_code}"] == "https://example.com"


def test_resolve_from_repository_when_cache_miss() -> None:
    service, cache, repo = _make_service()

    link = asyncio.run(service.shorten("https://example.com"))
    cache._store.clear()

    resolved = asyncio.run(service.resolve(link.short_code))

    assert resolved == "https://example.com"


def test_resolve_raises_when_missing() -> None:
    service, _cache, _repo = _make_service()

    try:
        asyncio.run(service.resolve("nope"))
        assert False, "expected LinkNotFoundError"
    except LinkNotFoundError:
        pass


def test_codec_roundtrip() -> None:
    for value in (0, 1, 42, 123456789):
        assert decode(encode(value)) == value


def test_link_is_frozen() -> None:
    link = Link(
        short_code="abc",
        long_url="https://example.com",
        created_at=datetime.now(timezone.utc),
    )

    try:
        link.long_url = "x"  # type: ignore[misc]
        assert False, "expected frozen dataclass"
    except Exception:
        pass
