import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "writerproj.settings")
django.setup()
from rest_framework.test import APIClient

def test_shorten(monkeypatch):
    import links.data_access as data_access
    import links.views as views
    monkeypatch.setattr(views, "insert_link", lambda code, url: None)
    monkeypatch.setattr(views, "get_long_url", lambda code: None)
    monkeypatch.setattr(views, "_redis_client", type("R", (), {"setex": lambda *a, **k: None})())
    client = APIClient()
    r = client.post("/api/shorten", {"url": "https://example.com"}, format="json")
    assert r.status_code == 201
    assert r.json()["code"]
