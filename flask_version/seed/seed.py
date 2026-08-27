import os
import redis
import psycopg2

DEMO = [
    ("exmpl", "https://example.com"),
    ("git", "https://github.com"),
    ("doc", "https://docs.python.org"),
    ("news", "https://news.ycombinator.com"),
]

DB_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
r = redis.Redis.from_url(REDIS_URL)

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
for code, url in DEMO:
    cur.execute("SELECT 1 FROM link WHERE code = %s", (code,))
    if cur.fetchone():
        print(f"skip existing {code}")
        continue
    cur.execute(
        "INSERT INTO link (code, long_url) VALUES (%s, %s)",
        (code, url),
    )
    r.setex(f"short:{code}", 3600, url)
    print(f"seeded {code} -> {url}")
conn.commit()
cur.close()
conn.close()
print("seed complete")
