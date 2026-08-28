# app/writer_main.py
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from app.infrastructure.containers import AppProvider
from app.presentation.writer_routes import router

app = FastAPI()
setup_dishka(make_async_container(AppProvider()), app)
app.include_router(router)


@app.get("/healthz")
def health() -> dict:
    return {"status": "ok"}
