from shared.domain.entities import Link
from shared.domain.interfaces import (
    CacheClient,
    IdGenerator,
    LinkRepository,
)
from shared.services.url_shortener import (
    LinkNotFoundError,
    UrlShortenerService,
)
