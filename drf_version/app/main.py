import os

from app.infrastructure.clients import get_cassandra_session, get_redis_client
from app.infrastructure.id_generator import SnowflakeIdGenerator
from app.infrastructure.redis_cache import RedisCacheClient
from app.infrastructure.scylla_repository import ScyllaLinkRepository
from app.services.url_shortener import UrlShortenerService


def build_service() -> UrlShortenerService:
    node_id = int(os.environ.get("NODE_ID", "1"))
    ttl = int(os.environ.get("CACHE_TTL", "3600"))

    id_generator = SnowflakeIdGenerator(node_id=node_id)
    repository = ScyllaLinkRepository(session=get_cassandra_session())
    cache = RedisCacheClient(get_redis_client())

    return UrlShortenerService(
        id_generator=id_generator,
        repository=repository,
        cache=cache,
        ttl=ttl,
    )
