import asyncio
from datetime import datetime, timezone

from app.domain.entities import Link
from app.infrastructure.clients import get_cassandra_session
from app.infrastructure.scylla_repository import ScyllaLinkRepository


DEMO_LINKS = [
    ("exmpl", "https://example.com"),
    ("git", "https://github.com"),
    ("doc", "https://docs.python.org"),
    ("news", "https://news.ycombinator.com"),
]


async def main() -> None:
    session = get_cassandra_session()
    repository = ScyllaLinkRepository(session=session)

    for code, url in DEMO_LINKS:
        if await repository.exists(code):
            print(f"skip {code}")

            continue

        await repository.save(
            Link(
                short_code=code,
                long_url=url,
                created_at=datetime.now(timezone.utc),
            )
        )
        print(f"seeded {code} -> {url}")

    print("seed complete")


if __name__ == "__main__":
    asyncio.run(main())
