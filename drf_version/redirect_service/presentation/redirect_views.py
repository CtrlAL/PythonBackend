import asyncio
from typing import Any

from django.http import Http404, HttpResponseRedirect
from django.views import View

from shared.services.url_shortener import LinkNotFoundError, UrlShortenerService


class RedirectView(View):
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

    def get(self, request: object, code: str) -> HttpResponseRedirect:
        assert self._service is not None

        try:
            long_url = asyncio.run(self._service.resolve(code))
        except LinkNotFoundError:
            raise Http404()

        return HttpResponseRedirect(long_url)
