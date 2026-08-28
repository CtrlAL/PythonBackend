import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import redis as redislib

try:
    import fakeredis
    redislib.Redis = fakeredis.FakeStrictRedis
except ImportError:
    pass

from app import app, get_long_url


@pytest.fixture
def client():
    r = redislib.Redis.from_url("redis://localhost:6379/0")
    r.flushdb()
    yield app.test_client()
    r.flushdb()


def test_redirect_from_redis(client):
    r = redislib.Redis.from_url("redis://localhost:6379/0")
    r.setex("short:abc", 3600, "https://example.com")
    resp = client.get("/abc")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://example.com"
