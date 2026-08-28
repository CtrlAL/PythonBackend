# fastapi_version/redirect/test_main.py
import os
os.environ.setdefault("SCYLLA_HOSTS", "127.0.0.1")
from fastapi.testclient import TestClient
from main import app
def test_redirect(monkeypatch):
    import common.data_access as data_access
    from main import _redis_client
    monkeypatch.setattr(data_access, "init_db", lambda: None)
    monkeypatch.setattr(data_access, "get_long_url", lambda code: "https://example.com")
    monkeypatch.setattr(_redis_client, "get", lambda *a, **k: None)
    monkeypatch.setattr(_redis_client, "setex", lambda *a, **k: None)
    c = TestClient(app)
    r = c.get("/abc", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com"
