# app/presentation/redirect_routes.py
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.services.url_shortener import LinkNotFoundError, UrlShortenerService

router = APIRouter(route_class=DishkaRoute)


@router.get("/{code}")
async def redirect(
    code: str,
    service: FromDishka[UrlShortenerService],
) -> RedirectResponse:
    try:
        long_url = await service.resolve(code)

    except LinkNotFoundError:
        raise HTTPException(status_code=404, detail="not found")

    return RedirectResponse(long_url, status_code=302)
