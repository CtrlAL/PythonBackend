# fastapi_version/seed/seed.py
import asyncio
import os
from datetime import datetime, timezone

from shared.domain.entities import Link
from shared.infrastructure.redis_cache import RedisCacheClient
from shared.infrastructure.scylla_repository import ScyllaLinkRepository

DEMO_LINKS = [
    ("exmpl", "https://example.com"),
    ("git", "https://github.com"),
    ("doc", "https://docs.python.org"),
    ("news", "https://news.ycombinator.com"),
]


async def main() -> None:
    hosts = os.environ["SCYLLA_HOSTS"].split(",")
    repository = ScyllaLinkRepository(hosts=hosts)

    url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    cache = RedisCacheClient(url=url)

    for code, long_url in DEMO_LINKS:

        if await repository.exists(code):
            print("skip", code)
            continue

        await repository.save(
            Link(
                short_code=code,
                long_url=long_url,
                created_at=datetime.now(timezone.utc),
            )
        )
        await cache.set_with_ttl(f"short:{code}", long_url, 3600)
        print("seeded", code, "->", long_url)

    print("seed complete")


if __name__ == "__main__":
    asyncio.run(main())
