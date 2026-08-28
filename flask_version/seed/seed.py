import os
import redis
import psycopg2

DEMO_LINKS = [
    ("exmpl", "https://example.com"),
    ("git", "https://github.com"),
    ("doc", "https://docs.python.org"),
    ("news", "https://news.ycombinator.com"),
]

DB_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)

connection = psycopg2.connect(DB_URL)
cursor = connection.cursor()
for code, url in DEMO_LINKS:
    cur.execute("SELECT 1 FROM link WHERE code = %s", (code,))
    if cur.fetchone():
        print(f"skip existing {code}")
        continue
    cur.execute(
        "INSERT INTO link (code, long_url) VALUES (%s, %s)",
        (code, url),
    )
    redis_client.setex(f"short:{code}", 3600, url)
    print(f"seeded {code} -> {url}")

connection.commit()
cursor.close()
connection.close()
print("seed complete")
