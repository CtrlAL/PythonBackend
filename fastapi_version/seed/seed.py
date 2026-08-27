# fastapi_version/seed/seed.py
import os, cassandra.cluster, redis
DEMO = [
    ("exmpl", "https://example.com"),
    ("git", "https://github.com"),
    ("doc", "https://docs.python.org"),
    ("news", "https://news.ycombinator.com"),
]
hosts = os.environ["SCYLLA_HOSTS"].split(",")
r = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
cl = cassandra.cluster.Cluster(hosts)
sess = cl.connect()
sess.execute("CREATE KEYSPACE IF NOT EXISTS urlshort WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
sess.set_keyspace("urlshort")
sess.execute("CREATE TABLE IF NOT EXISTS links (code text PRIMARY KEY, long_url text)")
for code, url in DEMO:
    if sess.execute("SELECT code FROM links WHERE code=%s", (code,)).one():
        print("skip", code); continue
    sess.execute("INSERT INTO links (code, long_url) VALUES (%s, %s)", (code, url))
    r.setex(f"short:{code}", 3600, url)
    print("seeded", code, "->", url)
print("seed complete")
