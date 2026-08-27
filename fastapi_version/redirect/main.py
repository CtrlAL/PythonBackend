# fastapi_version/redirect/main.py
import os, redis
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi import HTTPException
from common import dal

app = FastAPI()
_redis = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))

@app.on_event("startup")
def startup():
    dal.init_db()

@app.get("/{code}")
def redir(code: str):
    cached = _redis.get(f"short:{code}")
    if cached:
        return RedirectResponse(cached.decode(), status_code=302)
    url = dal.get_long_url(code)
    if not url:
        raise HTTPException(status_code=404, detail="not found")
    _redis.setex(f"short:{code}", 3600, url)
    return RedirectResponse(url, status_code=302)

@app.get("/healthz")
def health():
    return {"status": "ok"}
