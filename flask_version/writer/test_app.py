import os, pytest
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("BASE_URL", "http://localhost")
from app import app, db, Link

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_shorten(client):
    r = client.post("/api/shorten", json={"url": "https://example.com"})
    assert r.status_code == 201
    body = r.get_json()
    assert body["code"]
    assert body["short_url"].endswith(body["code"])
