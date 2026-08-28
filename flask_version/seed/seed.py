import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.domain.entities import Link
from shared.domain.codecs import encode
from shared.infrastructure.database import get_connection
from shared.infrastructure.postgres_repository import PostgresLinkRepository

DEMO_LINKS = [
    ("exmpl", "https://example.com"),
    ("git", "https://github.com"),
    ("doc", "https://docs.python.org"),
    ("news", "https://news.ycombinator.com"),
]


def main() -> None:
    connection = get_connection()
    repository = PostgresLinkRepository(connection)

    for code, url in DEMO_LINKS:
        link = Link(
            short_code=code,
            long_url=url,
            created_at=datetime.now(timezone.utc),
        )

        asyncio.run(repository.save(link))
        print(f"seeded {code} -> {url}")

    connection.close()
    print("seed complete")


if __name__ == "__main__":
    main()
