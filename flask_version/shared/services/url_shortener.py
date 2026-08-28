from datetime import datetime, timezone

from shared.domain.codecs import encode
from shared.domain.entities import Link
from shared.domain.interfaces import CacheClient, IdGenerator, LinkRepository


class LinkNotFoundError(Exception):
    pass


class UrlShortenerService:
    def __init__(
        self,
        id_generator: IdGenerator,
        repository: LinkRepository,
        cache: CacheClient,
        ttl: int = 3600,
    ) -> None:
        self._id_generator = id_generator
        self._repository = repository
        self._cache = cache
        self._ttl = ttl

    async def shorten(self, long_url: str) -> Link:
        link_id = self._id_generator.generate()
        code = encode(link_id)

        link = Link(
            short_code=code,
            long_url=long_url,
            created_at=datetime.now(timezone.utc),
        )

        await self._repository.save(link)
        await self._cache.set_with_ttl(f"short:{code}", long_url, self._ttl)

        return link

    async def resolve(self, code: str) -> str:
        cached = await self._cache.get(f"short:{code}")

        if cached is not None:
            return cached

        link = await self._repository.get_by_code(code)

        if link is None:
            raise LinkNotFoundError(code)

        await self._cache.set_with_ttl(f"short:{code}", link.long_url, self._ttl)

        return link.long_url
