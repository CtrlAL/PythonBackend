# fastapi_version/writer/test_main.py
import os
os.environ.setdefault("SCYLLA_HOSTS", "127.0.0.1")
from fastapi.testclient import TestClient
from main import app
def test_shorten(monkeypatch):
    import common.data_access as data_access
    from main import _redis_client
    monkeypatch.setattr(data_access, "init_db", lambda: None)
    monkeypatch.setattr(data_access, "insert_link", lambda c, u: None)
    monkeypatch.setattr(_redis_client, "setex", lambda *a, **k: None)
    c = TestClient(app)
    r = c.post("/api/shorten", json={"url": "https://example.com"})
    assert r.status_code == 201
    assert r.json()["code"]
