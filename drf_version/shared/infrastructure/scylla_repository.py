import asyncio
from datetime import datetime

from typing import Any

from shared.domain.entities import Link
from shared.domain.interfaces import LinkRepository

_EPOCH = datetime.fromtimestamp(0)


class ScyllaLinkRepository:
    def __init__(
        self,
        session: Any = None,
        hosts: list[str] | None = None,
    ) -> None:
        if session is not None:
            self._session = session
        else:
            from shared.infrastructure.clients import get_cassandra_session

            self._session = get_cassandra_session(hosts)

    async def save(self, link: Link) -> None:
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(None, self._sync_save, link)

    async def get_by_code(self, code: str) -> Link | None:
        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(None, self._sync_get_by_code, code)

    async def exists(self, code: str) -> bool:
        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(None, self._sync_exists, code)

    def _sync_save(self, link: Link) -> None:
        self._session.execute(
            "INSERT INTO links (code, long_url) VALUES (%s, %s)",
            (link.short_code, link.long_url),
        )

    def _sync_get_by_code(self, code: str) -> Link | None:
        row = self._session.execute(
            "SELECT code, long_url FROM links WHERE code=%s", (code,)
        ).one()

        if row is None:
            return None

        return Link(
            short_code=row["code"],
            long_url=row["long_url"],
            created_at=_EPOCH,
        )

    def _sync_exists(self, code: str) -> bool:
        row = self._session.execute(
            "SELECT code FROM links WHERE code=%s", (code,)
        ).one()

        return row is not None
