import os
import threading

from typing import Any


_cassandra_session: Any = None
_cassandra_lock = threading.Lock()

_redis_client: Any = None
_redis_lock = threading.Lock()


def get_cassandra_session(hosts: list[str] | None = None) -> Any:
    global _cassandra_session

    if _cassandra_session is None:
        with _cassandra_lock:
            if _cassandra_session is None:
                import cassandra.cluster
                from cassandra.query import dict_factory

                if hosts is None:
                    hosts = os.environ.get(
                        "SCYLLA_HOSTS", "127.0.0.1"
                    ).split(",")

                cluster = cassandra.cluster.Cluster(hosts)
                session = cluster.connect()
                session.row_factory = dict_factory
                session.execute(
                    "CREATE KEYSPACE IF NOT EXISTS urlshort WITH replication = "
                    "{'class':'SimpleStrategy','replication_factor':1}"
                )
                session.set_keyspace("urlshort")
                session.execute(
                    "CREATE TABLE IF NOT EXISTS links "
                    "(code text PRIMARY KEY, long_url text)"
                )

                _cassandra_session = session

    return _cassandra_session


def get_redis_client() -> Any:
    global _redis_client

    if _redis_client is None:
        with _redis_lock:
            if _redis_client is None:
                import redis.asyncio

                _redis_client = redis.asyncio.Redis.from_url(
                    os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
                )

    return _redis_client
