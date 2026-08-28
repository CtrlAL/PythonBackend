from datetime import datetime, timezone

from shared.domain.codecs import decode, encode
from shared.domain.entities import Link
from shared.services.url_shortener import (
    LinkNotFoundError,
    UrlShortenerService,
)
