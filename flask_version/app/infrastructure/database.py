import os
import re
from typing import Optional

import psycopg2
import redis.asyncio as aioredis

_CONNECTION: Optional["psycopg2.extensions.connection"] = None
_CLIENT: Optional["aioredis.Redis"] = None

DSN_PATTERN = re.compile(r"^postgresql\+[a-z]+")


def _normalize_dsn(dsn: str) -> str:
    return DSN_PATTERN.sub("postgresql", dsn)


def get_connection() -> "psycopg2.extensions.connection":
    global _CONNECTION

    if _CONNECTION is None:
        _CONNECTION = psycopg2.connect(
            _normalize_dsn(os.environ["DATABASE_URL"])
        )

    return _CONNECTION


def get_redis_client() -> "aioredis.Redis":
    global _CLIENT

    if _CLIENT is None:
        _CLIENT = aioredis.Redis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        )

    return _CLIENT
