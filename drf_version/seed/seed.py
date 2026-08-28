import os, redis
import cassandra.cluster

DEMO_LINKS = [
    ("exmpl", "https://example.com"),
    ("git", "https://github.com"),
    ("doc", "https://docs.python.org"),
    ("news", "https://news.ycombinator.com"),
]
hosts = os.environ["SCYLLA_HOSTS"].split(",")
redis_client = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
cluster = cassandra.cluster.Cluster(hosts)
session = cluster.connect()
session.execute("CREATE KEYSPACE IF NOT EXISTS urlshort WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
session.set_keyspace("urlshort")
session.execute("CREATE TABLE IF NOT EXISTS links (code text PRIMARY KEY, long_url text)")
for code, url in DEMO_LINKS:
    existing = session.execute("SELECT code FROM links WHERE code=%s", (code,)).one()
    if existing:
        print(f"skip {code}")
        continue
    session.execute("INSERT INTO links (code, long_url) VALUES (%s, %s)", (code, url))
    redis_client.setex(f"short:{code}", 3600, url)
    print(f"seeded {code} -> {url}")
print("seed complete")
