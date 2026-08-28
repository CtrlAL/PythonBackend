# fastapi_version/writer/main.py
import os
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from common.snowflake import Snowflake
from common.base62 import encode
from common import data_access

app = FastAPI()
_redis_client = redis.Redis.from_url(
    os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
)
_id_generator = Snowflake(node_id=int(os.environ.get("NODE_ID", "1")))
_base_url = os.environ.get("BASE_URL", "http://localhost")


class ShortenRequest(BaseModel):
    url: HttpUrl


@app.on_event("startup")
def startup():
    data_access.init_db()


@app.post("/api/shorten", status_code=201)
def shorten(payload: ShortenRequest):
    code = encode(_id_generator.next_id())
    data_access.insert_link(code, str(payload.url))
    _redis_client.setex(f"short:{code}", 3600, str(payload.url))

    return {"code": code, "short_url": f"{_base_url}/{code}"}


@app.get("/healthz")
def health():
    return {"status": "ok"}
