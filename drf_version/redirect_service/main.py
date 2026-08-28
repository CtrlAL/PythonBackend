import os

import django
from django.conf import settings


settings.configure(
    DEBUG=os.environ.get("DEBUG", "True") == "True",
    ALLOWED_HOSTS=["*"],
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-insecure-key-redirect"),
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
    ],
    MIDDLEWARE=["django.middleware.common.CommonMiddleware"],
    ROOT_URLCONF="redirect_service.main",
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {},
        }
    ],
    WSGI_APPLICATION="redirect_service.main.application",
    DATABASES={},
    LANGUAGE_CODE="en-us",
    TIME_ZONE="UTC",
    STATIC_URL="/static/",
    DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
)

from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse
from django.urls import path

from shared.infrastructure.clients import (
    get_cassandra_session,
    get_redis_client,
)
from shared.infrastructure.id_generator import SnowflakeIdGenerator
from shared.infrastructure.redis_cache import RedisCacheClient
from shared.infrastructure.scylla_repository import ScyllaLinkRepository
from shared.services.url_shortener import UrlShortenerService
from redirect_service.presentation.redirect_views import RedirectView


def _build_service() -> UrlShortenerService:
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


django.setup()

service = _build_service()

urlpatterns = [
    path("healthz", lambda r: HttpResponse("ok")),
    path("<str:code>", RedirectView.as_view(service=service)),
]

application = get_wsgi_application()
