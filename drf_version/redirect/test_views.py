import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "redirectproj.settings")
django.setup()
from django.test import Client

def test_redirect(monkeypatch):
    import links.views as views
    monkeypatch.setattr(views, "get_long_url", lambda code: "https://example.com")
    monkeypatch.setattr(views, "_redis_client", type("R", (), {"get": lambda *a, **k: None, "setex": lambda *a, **k: None})())
    c = Client()
    resp = c.get("/abc")
    assert resp.status_code == 302
    assert resp["Location"] == "https://example.com"
