import asyncio
from datetime import datetime, timezone
from typing import Optional

import psycopg2

from shared.domain.entities import Link
from shared.domain.interfaces import LinkRepository


class PostgresLinkRepository:
    def __init__(self, connection: "psycopg2.extensions.connection") -> None:
        self._connection = connection

    def _save_sync(self, link: Link) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO link (code, long_url) VALUES (%s, %s) "
                "ON CONFLICT (code) DO NOTHING",
                (link.short_code, link.long_url),
            )

        self._connection.commit()

    def _get_sync(self, code: str) -> Optional[Link]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT code, long_url FROM link WHERE code = %s",
                (code,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return Link(
            short_code=row[0],
            long_url=row[1],
            created_at=datetime.now(timezone.utc),
        )

    def _exists_sync(self, code: str) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM link WHERE code = %s", (code,))
            return cursor.fetchone() is not None

    async def save(self, link: Link) -> None:
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(None, self._save_sync, link)

    async def get_by_code(self, code: str) -> Optional[Link]:
        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(None, self._get_sync, code)

    async def exists(self, code: str) -> bool:
        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(None, self._exists_sync, code)
