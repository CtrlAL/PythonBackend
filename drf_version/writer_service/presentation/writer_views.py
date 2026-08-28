import asyncio
import os
from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.presentation.schemas import ShortenRequest, ShortenResponse
from shared.services.url_shortener import UrlShortenerService


class ShortenView(APIView):
    _service: UrlShortenerService | None = None

    @classmethod
    def as_view(cls, **initkwargs: Any) -> Any:
        service = initkwargs.pop("service", None)

        if service is not None:
            cls = type(cls.__name__, (cls,), {"_service": service})

        return super().as_view(**initkwargs)

    def __init__(self, **kwargs: Any) -> None:
        provided = kwargs.pop("service", None)
        self._service = provided or getattr(type(self), "_service", None)

        super().__init__(**kwargs)

    def post(self, request: Request) -> Response:
        assert self._service is not None

        payload = ShortenRequest(**request.data)
        link = asyncio.run(self._service.shorten(payload.url))

        base_url = os.environ.get("BASE_URL", "http://localhost")
        body = ShortenResponse(
            code=link.short_code,
            short_url=f"{base_url}/{link.short_code}",
        )

        return Response(body.model_dump(), status=status.HTTP_201_CREATED)
