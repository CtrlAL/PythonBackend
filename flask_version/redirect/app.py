import os
import redis
import psycopg2
from flask import Flask, redirect, abort

app = Flask(__name__)
redis_client = redis.Redis.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379/0")
)
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")


def get_long_url(code: str):
    cached = redis_client.get(f"short:{code}")
    if cached:
        return cached.decode()

    if DB_URL.startswith("sqlite"):
        return None

    connection = psycopg2.connect(DB_URL)

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT long_url FROM link WHERE code = %s", (code,))
        row = cursor.fetchone()
    finally:
        connection.close()

    if not row:
        return None

    redis_client.setex(f"short:{code}", 3600, row[0])
    return row[0]


@app.route("/<code>")
def redir(code):
    url = get_long_url(code)
    if not url:
        abort(404)

    return redirect(url, code=302)


@app.route("/healthz", methods=["GET"])
def health():
    return "ok", 200
