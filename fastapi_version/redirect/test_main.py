# fastapi_version/redirect/test_main.py
import os
os.environ.setdefault("SCYLLA_HOSTS", "127.0.0.1")
from fastapi.testclient import TestClient
from main import app
def test_redirect(monkeypatch):
    from common import dal
    from main import _redis
    monkeypatch.setattr(dal, "init_db", lambda: None)
    monkeypatch.setattr(dal, "get_long_url", lambda code: "https://example.com")
    monkeypatch.setattr(_redis, "get", lambda *a, **k: None)
    monkeypatch.setattr(_redis, "setex", lambda *a, **k: None)
    c = TestClient(app)
    r = c.get("/abc", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com"
