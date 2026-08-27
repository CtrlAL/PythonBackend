import os
import redis
import psycopg2
from flask import Flask, redirect, abort

app = Flask(__name__)
r = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")

def get_long_url(code: str):
    cached = r.get(f"short:{code}")
    if cached:
        return cached.decode()
    if DB_URL.startswith("sqlite"):
        return None
    conn = psycopg2.connect(DB_URL)
    try:
        cur = conn.cursor()
        cur.execute("SELECT long_url FROM link WHERE code = %s", (code,))
        row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        return None
    r.setex(f"short:{code}", 3600, row[0])
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
