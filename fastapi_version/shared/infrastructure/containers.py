# shared/infrastructure/containers.py
import os

from dishka import Provider, Scope, provide

from shared.domain.interfaces import CacheClient, IdGenerator, LinkRepository
from shared.infrastructure.id_generator import SnowflakeIdGenerator
from shared.infrastructure.redis_cache import RedisCacheClient
from shared.infrastructure.scylla_repository import ScyllaLinkRepository
from shared.services.url_shortener import UrlShortenerService


class AppProvider(Provider):
    @provide(provides=IdGenerator, scope=Scope.APP)
    def provide_id_generator(self) -> SnowflakeIdGenerator:
        node_id = int(os.environ.get("NODE_ID", "1"))

        return SnowflakeIdGenerator(node_id=node_id)

    @provide(provides=LinkRepository, scope=Scope.APP)
    def provide_repository(self) -> ScyllaLinkRepository:
        hosts = os.environ.get("SCYLLA_HOSTS", "127.0.0.1").split(",")

        return ScyllaLinkRepository(hosts=hosts)

    @provide(provides=CacheClient, scope=Scope.APP)
    def provide_cache(self) -> RedisCacheClient:
        url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

        return RedisCacheClient(url=url)

    @provide(provides=UrlShortenerService, scope=Scope.REQUEST)
    def provide_service(
        self,
        id_generator: IdGenerator,
        repository: LinkRepository,
        cache: CacheClient,
    ) -> UrlShortenerService:
        return UrlShortenerService(
            id_generator=id_generator,
            repository=repository,
            cache=cache,
        )
