import os

from flask import Flask

from app.infrastructure.database import get_connection, get_redis_client
from app.infrastructure.id_generator import SnowflakeIdGenerator
from app.infrastructure.postgres_repository import PostgresLinkRepository
from app.infrastructure.redis_cache import RedisCacheClient
from app.presentation.redirect_routes import create_redirect_blueprint
from app.presentation.writer_routes import create_writer_blueprint
from app.services.url_shortener import UrlShortenerService


def create_app(
    include_writer: bool = True,
    include_redirect: bool = True,
) -> Flask:
    app = Flask(__name__)

    connection = get_connection()
    redis_client = get_redis_client()

    id_generator = SnowflakeIdGenerator(
        node_id=int(os.environ.get("NODE_ID", "0"))
    )
    repository = PostgresLinkRepository(connection)
    cache = RedisCacheClient(redis_client)
    service = UrlShortenerService(id_generator, repository, cache)

    base_url = os.environ.get("BASE_URL", "http://localhost")

    if include_writer:
        app.register_blueprint(
            create_writer_blueprint(service, base_url)
        )

    if include_redirect:
        app.register_blueprint(create_redirect_blueprint(service))

    return app
