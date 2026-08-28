# writer_service/presentation/writer_routes.py
import os

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from shared.presentation.schemas import ShortenRequest, ShortenResponse
from shared.services.url_shortener import UrlShortenerService

router = APIRouter(route_class=DishkaRoute)


@router.post("/api/shorten", status_code=201, response_model=ShortenResponse)
async def shorten(
    payload: ShortenRequest,
    service: FromDishka[UrlShortenerService],
) -> ShortenResponse:
    link = await service.shorten(str(payload.url))
    base_url = os.environ.get("BASE_URL", "http://localhost")

    return ShortenResponse(
        code=link.short_code,
        short_url=f"{base_url}/{link.short_code}",
    )
