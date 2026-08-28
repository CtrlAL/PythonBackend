# redirect_service/main.py
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from redirect_service.presentation.redirect_routes import router
from shared.infrastructure.containers import AppProvider

app = FastAPI()
setup_dishka(make_async_container(AppProvider()), app)
app.include_router(router)


@app.get("/healthz")
def health() -> dict:
    return {"status": "ok"}
