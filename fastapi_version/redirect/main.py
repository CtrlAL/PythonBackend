# fastapi_version/redirect/main.py
import os
import redis
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi import HTTPException
from common import data_access

app = FastAPI()
_redis_client = redis.Redis.from_url(
    os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
)


@app.on_event("startup")
def startup():
    data_access.init_db()


@app.get("/{code}")
def redir(code: str):
    cached_url = _redis_client.get(f"short:{code}")

    if cached_url:
        return RedirectResponse(cached_url.decode(), status_code=302)

    long_url = data_access.get_long_url(code)

    if not long_url:
        raise HTTPException(status_code=404, detail="not found")

    _redis_client.setex(f"short:{code}", 3600, long_url)

    return RedirectResponse(long_url, status_code=302)


@app.get("/healthz")
def health():
    return {"status": "ok"}
