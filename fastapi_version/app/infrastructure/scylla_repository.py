# app/infrastructure/scylla_repository.py
import asyncio
import os
from datetime import datetime, timezone

from app.domain.entities import Link
from app.domain.interfaces import LinkRepository


class ScyllaLinkRepository(LinkRepository):
    def __init__(self, hosts: list[str] | None = None) -> None:
        from cassandra.cluster import Cluster
        from cassandra.query import dict_factory

        if hosts is None:
            hosts = os.environ.get("SCYLLA_HOSTS", "127.0.0.1").split(",")

        cluster = Cluster(hosts)
        self._session = cluster.connect()
        self._session.row_factory = dict_factory
        self._session.execute(
            "CREATE KEYSPACE IF NOT EXISTS urlshort WITH replication = "
            "{'class':'SimpleStrategy','replication_factor':1}"
        )
        self._session.set_keyspace("urlshort")
        self._session.execute(
            "CREATE TABLE IF NOT EXISTS links (code text PRIMARY KEY, long_url text)"
        )

    def _sync_save(self, link: Link) -> None:
        self._session.execute(
            "INSERT INTO links (code, long_url) VALUES (%s, %s)",
            (link.short_code, link.long_url),
        )

    def _sync_get(self, code: str) -> Link | None:
        row = self._session.execute(
            "SELECT code, long_url FROM links WHERE code=%s", (code,)
        ).one()

        if row is None:
            return None

        return Link(
            short_code=row["code"],
            long_url=row["long_url"],
            created_at=datetime.now(timezone.utc),
        )

    def _sync_exists(self, code: str) -> bool:
        row = self._session.execute(
            "SELECT code FROM links WHERE code=%s", (code,)
        ).one()

        return row is not None

    async def save(self, link: Link) -> None:
        loop = asyncio.get_running_loop()

        await loop.run_in_executor(None, self._sync_save, link)

    async def get_by_code(self, code: str) -> Link | None:
        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(None, self._sync_get, code)

    async def exists(self, code: str) -> bool:
        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(None, self._sync_exists, code)
