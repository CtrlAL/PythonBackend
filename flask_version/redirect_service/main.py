import os

from flask import Flask
from uvicorn.middleware.wsgi import WSGIMiddleware

from shared.infrastructure.database import get_connection, get_redis_client
from shared.infrastructure.id_generator import SnowflakeIdGenerator
from shared.infrastructure.postgres_repository import PostgresLinkRepository
from shared.infrastructure.redis_cache import RedisCacheClient
from shared.services.url_shortener import UrlShortenerService
from redirect_service.presentation.redirect_routes import (
    create_redirect_blueprint,
)


def create_app() -> Flask:
    app = Flask(__name__)

    connection = get_connection()
    redis_client = get_redis_client()

    id_generator = SnowflakeIdGenerator(
        node_id=int(os.environ.get("NODE_ID", "0"))
    )
    repository = PostgresLinkRepository(connection)
    cache = RedisCacheClient(redis_client)
    service = UrlShortenerService(id_generator, repository, cache)

    app.register_blueprint(create_redirect_blueprint(service))

    return app


flask_app = create_app()
app = WSGIMiddleware(flask_app)
