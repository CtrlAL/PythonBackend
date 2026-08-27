# fastapi_version/writer/main.py
import os, redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from common.snowflake import Snowflake
from common.base62 import encode
from common import dal

app = FastAPI()
_redis = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
_sf = Snowflake(node_id=int(os.environ.get("NODE_ID", "1")))
_BASE = os.environ.get("BASE_URL", "http://localhost")

class Req(BaseModel):
    url: HttpUrl

@app.on_event("startup")
def startup():
    dal.init_db()

@app.post("/api/shorten", status_code=201)
def shorten(body: Req):
    code = encode(_sf.next_id())
    dal.insert_link(code, str(body.url))
    _redis.setex(f"short:{code}", 3600, str(body.url))
    return {"code": code, "short_url": f"{_BASE}/{code}"}

@app.get("/healthz")
def health():
    return {"status": "ok"}
