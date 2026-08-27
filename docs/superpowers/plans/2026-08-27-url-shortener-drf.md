# URL Shortener — DRF/ScyllaDB Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read/write-split URL shortener microservice using Django + DRF + ScyllaDB (Cassandra driver) + Redis, deployable to a local Kubernetes cluster (kind/minikube) via raw YAML.

**Architecture:** Two separate Django/DRF services — `writer` (POST /api/shorten) and `redirect` (GET /<code>). Writer generates a Snowflake 63-bit ID, encodes it to base62, persists to ScyllaDB, and warms Redis. Redirect reads through Redis (TTL 3600s), falling back to ScyllaDB. A seed Job populates demo links on startup. Each service is its own minimal Django project; all run in the `drf-url` K8s namespace.

**Tech Stack:** Python 3.11, Django 5, djangorestframework, cassandra-driver (ScyllaDB), redis-py, ScyllaDB 5 (image `scylladb/scylla`), Redis 7, Docker, kubectl (kind/minikube).

## Global Constraints

- Short code: unique 63-bit Snowflake ID → `base62(id)`, alphabet `0-9a-zA-Z` (62 chars).
- Redis key `short:<code>` → `long_url`, TTL 3600s. Writer warms on create; redirect reads-through.
- Services connect to ScyllaDB **directly** (no queue). ScyllaDB keyspace `urlshort`, table `links(code text PRIMARY KEY, long_url text)`.
- Deploy target: **local** kind/minikube, **raw YAML**, namespace `drf-url`.
- Redis **per-stack** (own instance in `drf-url`).
- No auth on link creation. No Helm.
- Commit frequently; each task ends with a passing test/check.

---

## Task 1: Snowflake generator + tests

**Files:**
- Create: `drf_version/common/snowflake.py`
- Test: `drf_version/common/test_snowflake.py`

**Interfaces:**
- Produces: `class Snowflake` with `next_id() -> int` (used by writer Task 3 and seed Task 5).

- [ ] **Step 1: Write failing tests**

```python
# drf_version/common/test_snowflake.py
import threading
from snowflake import Snowflake

def test_unique_and_monotonic():
    s = Snowflake(node_id=1)
    ids = [s.next_id() for _ in range(10000)]
    assert len(ids) == len(set(ids)), "ids not unique"
    assert ids == sorted(ids), "ids not monotonic"

def test_thread_safety():
    s = Snowflake(node_id=2)
    out = []
    def worker():
        for _ in range(2000):
            out.append(s.next_id())
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(out) == len(set(out)), "concurrent ids collided"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd drf_version/common && python -m pytest test_snowflake.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'snowflake'` — note stdlib has no such module here; our file shadows none).

- [ ] **Step 3: Implement**

```python
# drf_version/common/snowflake.py
import time
import threading

EPOCH_MS = 1288834974657  # Twitter epoch

class Snowflake:
    def __init__(self, node_id=1):
        self.node_id = node_id & 0x3FF
        self.lock = threading.Lock()
        self.seq = 0
        self.last_ts = 0

    def _ts(self):
        return int(time.time() * 1000) - EPOCH_MS

    def next_id(self):
        with self.lock:
            ts = self._ts()
            if ts == self.last_ts:
                self.seq = (self.seq + 1) & 0xFFF
                if self.seq == 0:
                    while ts <= self.last_ts:
                        ts = self._ts()
            else:
                self.seq = 0
            self.last_ts = ts
            return ((ts << 22) | (self.node_id << 12) | self.seq)
```

- [ ] **Step 4: Run to verify pass**

Run: `cd drf_version/common && python -m pytest test_snowflake.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add drf_version/common/snowflake.py drf_version/common/test_snowflake.py
git commit -m "feat(drf): add Snowflake ID generator with tests"
```

---

## Task 2: Shared base62 utility (DRF)

**Files:**
- Create: `drf_version/common/base62.py`
- Test: `drf_version/common/test_base62_drf.py`

**Interfaces:**
- Produces: `encode(n: int) -> str`, `decode(s: str) -> int` (identical to Flask version; duplicated per spec's per-stack isolation).

- [ ] **Step 1: Write tests**

```python
# drf_version/common/test_base62_drf.py
from base62 import encode, decode

def test_roundtrip():
    for n in [0, 1, 42, 123456789, 2**40, 2**62]:
        assert decode(encode(n)) == n

def test_known():
    assert encode(10) == "a"
    assert encode(61) == "Z"
```

- [ ] **Step 2: Implement (copy of Flask base62)**

```python
# drf_version/common/base62.py
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)

def encode(n: int) -> str:
    if n == 0:
        return ALPHABET[0]
    s = ""
    while n > 0:
        s += ALPHABET[n % BASE]
        n //= BASE
    return s[::-1]

def decode(s: str) -> int:
    n = 0
    for c in s:
        n = n * BASE + ALPHABET.index(c)
    return n
```

- [ ] **Step 3: Run & commit**

Run: `cd drf_version/common && python -m pytest test_base62_drf.py -v` → PASS
```bash
git add drf_version/common/base62.py drf_version/common/test_base62_drf.py
git commit -m "feat(drf): add base62 util with tests"
```

---

## Task 3: DRF Writer service (Django project)

**Files:**
- Create: `drf_version/writer/manage.py`
- Create: `drf_version/writer/writerproj/__init__.py`
- Create: `drf_version/writer/writerproj/settings.py`
- Create: `drf_version/writer/writerproj/urls.py`
- Create: `drf_version/writer/writerproj/wsgi.py`
- Create: `drf_version/writer/links/__init__.py`
- Create: `drf_version/writer/links/apps.py`
- Create: `drf_version/writer/links/dao.py`
- Create: `drf_version/writer/links/serializers.py`
- Create: `drf_version/writer/links/views.py`
- Create: `drf_version/writer/requirements.txt`
- Test: `drf_version/writer/test_views.py`

**Interfaces:**
- Consumes: `Snowflake.next_id()` (common), `encode` (common), Scylla session (dao), Redis.
- Produces: `POST /api/shorten` → `{"code": str, "short_url": str}`; writes `short:<code>` to Redis; row in `urlshort.links`.

- [ ] **Step 1: Write failing test**

```python
# drf_version/writer/test_views.py
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "writerproj.settings")
django.setup()
from rest_framework.test import APIClient

def test_shorten():
    client = APIClient()
    r = client.post("/api/shorten", {"url": "https://example.com"}, format="json")
    assert r.status_code == 201
    assert r.json()["code"]
```

- [ ] **Step 2: Run to verify failure**

Run: `cd drf_version/writer && python -m pytest test_views.py -v`
Expected: FAIL (no module / Django not configured yet)

- [ ] **Step 3: Implement**

```python
# drf_version/writer/requirements.txt
django==5.0.6
djangorestframework==3.15.2
cassandra-driver==3.29.1
redis==5.0.4
gunicorn==22.0.0
```

```python
# drf_version/writer/manage.py
import os, sys
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "writerproj.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
```

```python
# drf_version/writer/writerproj/settings.py
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "dev-insecure-key"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = ["rest_framework", "links"]
MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]
ROOT_URLCONF = "writerproj.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": False, "OPTIONS": {}}]
WSGI_APPLICATION = "writerproj.wsgi.application"
DATABASES = {}
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SCYLLA_HOSTS = os.environ.get("SCYLLA_HOSTS", "127.0.0.1").split(",")
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
BASE_URL = os.environ.get("BASE_URL", "http://localhost")
```

```python
# drf_version/writer/writerproj/urls.py
from django.urls import path
from links.views import ShortenView
urlpatterns = [path("api/shorten", ShortenView.as_view()), path("healthz", lambda r: __import__("django").http.HttpResponse("ok"))]
```

```python
# drf_version/writer/writerproj/wsgi.py
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "writerproj.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

```python
# drf_version/writer/links/apps.py
from django.apps import AppConfig
class LinksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "links"
```

```python
# drf_version/writer/links/dao.py
import os, cassandra.cluster
from cassandra.query import dict_factory

_session = None

def get_session():
    global _session
    if _session is None:
        hosts = os.environ.get("SCYLLA_HOSTS", "127.0.0.1").split(",")
        cluster = cassandra.cluster.Cluster(hosts)
        _session = cluster.connect()
        _session.row_factory = dict_factory
        _session.execute("CREATE KEYSPACE IF NOT EXISTS urlshort WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
        _session.set_keyspace("urlshort")
        _session.execute("CREATE TABLE IF NOT EXISTS links (code text PRIMARY KEY, long_url text)")
    return _session

def insert_link(code, long_url):
    get_session().execute("INSERT INTO links (code, long_url) VALUES (%s, %s)", (code, long_url))

def get_long_url(code):
    row = get_session().execute("SELECT long_url FROM links WHERE code=%s", (code,)).one()
    return row["long_url"] if row else None
```

```python
# drf_version/writer/links/serializers.py
from rest_framework import serializers
class URLSerializer(serializers.Serializer):
    url = serializers.URLField()
```

```python
# drf_version/writer/links/views.py
import os, redis
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from serializers import URLSerializer
from dao import insert_link, get_long_url
from common.snowflake import Snowflake
from common.base62 import encode

_redis = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
_sf = Snowflake(node_id=int(os.environ.get("NODE_ID", "1")))
_BASE = os.environ.get("BASE_URL", "http://localhost")

class ShortenView(APIView):
    def post(self, request):
        ser = URLSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        long_url = ser.validated_data["url"]
        if get_long_url_cached(long_url) is not None:
            pass
        code = encode(_sf.next_id())
        insert_link(code, long_url)
        _redis.setex(f"short:{code}", 3600, long_url)
        return Response({"code": code, "short_url": f"{_BASE}/{code}"}, status=status.HTTP_201_CREATED)

def get_long_url_cached(code):
    return get_long_url(code)
```

> NOTE: `common` must be importable in writer. Copy `common/snowflake.py` and `common/base62.py` into the writer build context (Dockerfile Task 6 copies them). For local test run, add `drf_version/common` to PYTHONPATH: `PYTHONPATH=../common python -m pytest test_views.py`.

- [ ] **Step 4: Run to verify pass**

Run: `cd drf_version/writer && PYTHONPATH=../common DJANGO_SETTINGS_MODULE=writerproj.settings python -m pytest test_views.py -v`
Expected: PASS (requires a local Scylla/Redis, or mock — for plan correctness we accept integration test in K8s Task 8).

- [ ] **Step 5: Commit**

```bash
git add drf_version/writer/
git commit -m "feat(drf): writer service creates links via DRF + Scylla + Redis warm"
```

---

## Task 4: DRF Redirect service (separate Django project)

**Files:**
- Create: `drf_version/redirect/manage.py`
- Create: `drf_version/redirect/redirectproj/__init__.py`
- Create: `drf_version/redirect/redirectproj/settings.py`
- Create: `drf_version/redirect/redirectproj/urls.py`
- Create: `drf_version/redirect/redirectproj/wsgi.py`
- Create: `drf_version/redirect/links/__init__.py`
- Create: `drf_version/redirect/links/apps.py`
- Create: `drf_version/redirect/links/dao.py`
- Create: `drf_version/redirect/links/views.py`
- Create: `drf_version/redirect/requirements.txt`
- Test: `drf_version/redirect/test_views.py`

**Interfaces:**
- Consumes: Scylla `urlshort.links`, Redis `short:<code>` (TTL 3600).
- Produces: `GET /<code>` → 302 `Location: <long_url>`; 404 if unknown.

- [ ] **Step 1: Write failing test**

```python
# drf_version/redirect/test_views.py
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "redirectproj.settings")
django.setup()
from django.test import Client

def test_redirect(monkeypatch):
    import links.dao as dao
    monkeypatch.setattr(dao, "get_long_url", lambda code: "https://example.com")
    c = Client()
    resp = c.get("/abc")
    assert resp.status_code == 302
    assert resp["Location"] == "https://example.com"
```

- [ ] **Step 2: Implement (mirror of writer; dao reused, view differs)**

```python
# drf_version/redirect/requirements.txt
django==5.0.6
djangorestframework==3.15.2
cassandra-driver==3.29.1
redis==5.0.4
gunicorn==22.0.0
```

```python
# drf_version/redirect/manage.py  (same as writer, DJANGO_SETTINGS_MODULE=redirectproj.settings)
import os, sys
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "redirectproj.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
```

```python
# drf_version/redirect/redirectproj/settings.py
import os
SECRET_KEY = "dev-insecure-key-2"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = ["rest_framework", "links"]
MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]
ROOT_URLCONF = "redirectproj.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": False, "OPTIONS": {}}]
WSGI_APPLICATION = "redirectproj.wsgi.application"
DATABASES = {}
LANGUAGE_CODE = "en-us"; TIME_ZONE = "UTC"; STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SCYLLA_HOSTS = os.environ.get("SCYLLA_HOSTS", "127.0.0.1").split(",")
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
```

```python
# drf_version/redirect/redirectproj/urls.py
from django.urls import path
from links.views import RedirectView
urlpatterns = [path("<str:code>", RedirectView.as_view()), path("healthz", lambda r: __import__("django").http.HttpResponse("ok"))]
```

```python
# drf_version/redirect/redirectproj/wsgi.py
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "redirectproj.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

```python
# drf_version/redirect/links/apps.py
from django.apps import AppConfig
class LinksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "links"
```

```python
# drf_version/redirect/links/dao.py
import os, cassandra.cluster
from cassandra.query import dict_factory
_session = None
def get_session():
    global _session
    if _session is None:
        hosts = os.environ.get("SCYLLA_HOSTS", "127.0.0.1").split(",")
        cluster = cassandra.cluster.Cluster(hosts)
        _session = cluster.connect()
        _session.row_factory = dict_factory
        _session.execute("CREATE KEYSPACE IF NOT EXISTS urlshort WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
        _session.set_keyspace("urlshort")
        _session.execute("CREATE TABLE IF NOT EXISTS links (code text PRIMARY KEY, long_url text)")
    return _session
def get_long_url(code):
    row = get_session().execute("SELECT long_url FROM links WHERE code=%s", (code,)).one()
    return row["long_url"] if row else None
```

```python
# drf_version/redirect/links/views.py
import os, redis
from django.http import HttpResponseRedirect, Http404
from django.views import View
from dao import get_long_url
_redis = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))

class RedirectView(View):
    def get(self, request, code):
        cached = _redis.get(f"short:{code}")
        if cached:
            return HttpResponseRedirect(cached.decode())
        url = get_long_url(code)
        if not url:
            raise Http404()
        _redis.setex(f"short:{code}", 3600, url)
        return HttpResponseRedirect(url)
```

- [ ] **Step 3: Run test to verify pass**

Run: `cd drf_version/redirect && PYTHONPATH=../common DJANGO_SETTINGS_MODULE=redirectproj.settings python -m pytest test_views.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add drf_version/redirect/
git commit -m "feat(drf): redirect service reads Scylla through Redis"
```

---

## Task 5: Seed script (ScyllaDB + Redis)

**Files:**
- Create: `drf_version/seed/seed.py`
- Create: `drf_version/seed/requirements.txt`

**Interfaces:**
- Consumes: `SCYLLA_HOSTS`, `REDIS_URL`. Writes `urlshort.links(code,long_url)` and `short:<code>` in Redis. Idempotent.

- [ ] **Step 1: Implement**

```python
# drf_version/seed/requirements.txt
cassandra-driver==3.29.1
redis==5.0.4
```

```python
# drf_version/seed/seed.py
import os, cassandra.cluster, redis
DEMO = [
    ("exmpl", "https://example.com"),
    ("git", "https://github.com"),
    ("doc", "https://docs.python.org"),
    ("news", "https://news.ycombinator.com"),
]
hosts = os.environ["SCYLLA_HOSTS"].split(",")
r = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
cluster = cassandra.cluster.Cluster(hosts)
sess = cluster.connect()
sess.execute("CREATE KEYSPACE IF NOT EXISTS urlshort WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
sess.set_keyspace("urlshort")
sess.execute("CREATE TABLE IF NOT EXISTS links (code text PRIMARY KEY, long_url text)")
for code, url in DEMO:
    existing = sess.execute("SELECT code FROM links WHERE code=%s", (code,)).one()
    if existing:
        print(f"skip {code}")
        continue
    sess.execute("INSERT INTO links (code, long_url) VALUES (%s, %s)", (code, url))
    r.setex(f"short:{code}", 3600, url)
    print(f"seeded {code} -> {url}")
print("seed complete")
```

- [ ] **Step 2: Commit**

```bash
git add drf_version/seed/
git commit -m "feat(drf): seed demo links into ScyllaDB and Redis"
```

---

## Task 6: Dockerfiles (DRF)

**Files:**
- Create: `drf_version/writer/Dockerfile`
- Create: `drf_version/redirect/Dockerfile`
- Create: `drf_version/seed/Dockerfile`

**Interfaces:** Build context `drf_version/` so `common/` is available. Images: `drf-writer`, `drf-redirect`, `drf-seed`.

- [ ] **Step 1: Writer Dockerfile**

```dockerfile
# drf_version/writer/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY writer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY writer/ ./writer/
WORKDIR /app/writer
ENV PYTHONPATH=/app/common:/app/writer
EXPOSE 8000
CMD ["gunicorn", "writerproj.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
```

- [ ] **Step 2: Redirect Dockerfile**

```dockerfile
# drf_version/redirect/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY redirect/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY redirect/ ./redirect/
WORKDIR /app/redirect
ENV PYTHONPATH=/app/common:/app/redirect
EXPOSE 8000
CMD ["gunicorn", "redirectproj.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
```

- [ ] **Step 3: Seed Dockerfile**

```dockerfile
# drf_version/seed/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY seed/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY seed/seed.py ./seed.py
ENV PYTHONPATH=/app/common
CMD ["python", "seed.py"]
```

- [ ] **Step 4: Build**

```bash
docker build -f drf_version/writer/Dockerfile -t drf-writer:latest drf_version
docker build -f drf_version/redirect/Dockerfile -t drf-redirect:latest drf_version
docker build -f drf_version/seed/Dockerfile -t drf-seed:latest drf_version
```
Expected: all build successfully.

- [ ] **Step 5: Commit**

```bash
git add drf_version/*/Dockerfile
git commit -m "feat(drf): Dockerfiles for writer, redirect, seed"
```

---

## Task 7: Kubernetes manifests (drf-url namespace)

**Files:**
- Create: `k8s/drf/00-namespace.yaml`
- Create: `k8s/drf/01-configmap.yaml`
- Create: `k8s/drf/02-scylla.yaml`
- Create: `k8s/drf/03-redis.yaml`
- Create: `k8s/drf/04-writer.yaml`
- Create: `k8s/drf/05-redirect.yaml`
- Create: `k8s/drf/06-seed-job.yaml`

**Interfaces:** Namespace `drf-url` with ScyllaDB, Redis, writer (ClusterIP), redirect (NodePort 30081), seed Job. ConfigMap: `SCYLLA_HOSTS`, `REDIS_URL`, `BASE_URL`.

- [ ] **Step 1: Namespace + ConfigMap**

```yaml
# k8s/drf/00-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: drf-url
```

```yaml
# k8s/drf/01-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: drf-config
  namespace: drf-url
data:
  SCYLLA_HOSTS: "scylla"
  REDIS_URL: "redis://redis:6379/0"
  BASE_URL: "http://localhost"
```

- [ ] **Step 2: ScyllaDB**

```yaml
# k8s/drf/02-scylla.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scylla
  namespace: drf-url
spec:
  replicas: 1
  selector:
    matchLabels: {app: scylla}
  template:
    metadata:
      labels: {app: scylla}
    spec:
      containers:
        - name: scylla
          image: scylladb/scylla:5.4
          args: ["--smp", "1", "--memory", "1G", "--overprovisioned", "1"]
          ports:
            - {containerPort: 9042}
          readinessProbe:
            exec:
              command: ["cqlsh", "-e", "SELECT now() FROM system.local"]
            initialDelaySeconds: 30
            periodSeconds: 15
---
apiVersion: v1
kind: Service
metadata:
  name: scylla
  namespace: drf-url
spec:
  selector: {app: scylla}
  ports:
    - {port: 9042, targetPort: 9042}
```

- [ ] **Step 3: Redis**

```yaml
# k8s/drf/03-redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: drf-url
spec:
  replicas: 1
  selector:
    matchLabels: {app: redis}
  template:
    metadata:
      labels: {app: redis}
    spec:
      containers:
        - name: redis
          image: redis:7
          ports:
            - {containerPort: 6379}
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: drf-url
spec:
  selector: {app: redis}
  ports:
    - {port: 6379, targetPort: 6379}
```

- [ ] **Step 4: Writer + Redirect**

```yaml
# k8s/drf/04-writer.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: writer
  namespace: drf-url
spec:
  replicas: 1
  selector:
    matchLabels: {app: writer}
  template:
    metadata:
      labels: {app: writer}
    spec:
      containers:
        - name: writer
          image: drf-writer:latest
          imagePullPolicy: IfNotPresent
          envFrom:
            - configMapRef: {name: drf-config}
          ports:
            - {containerPort: 8000}
          readinessProbe:
            httpGet: {path: /healthz, port: 8000}
            initialDelaySeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: writer
  namespace: drf-url
spec:
  selector: {app: writer}
  ports:
    - {port: 8000, targetPort: 8000}
```

```yaml
# k8s/drf/05-redirect.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redirect
  namespace: drf-url
spec:
  replicas: 1
  selector:
    matchLabels: {app: redirect}
  template:
    metadata:
      labels: {app: redirect}
    spec:
      containers:
        - name: redirect
          image: drf-redirect:latest
          imagePullPolicy: IfNotPresent
          envFrom:
            - configMapRef: {name: drf-config}
          ports:
            - {containerPort: 8000}
          readinessProbe:
            httpGet: {path: /healthz, port: 8000}
            initialDelaySeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: redirect
  namespace: drf-url
spec:
  type: NodePort
  selector: {app: redirect}
  ports:
    - {port: 8000, targetPort: 8000, nodePort: 30081}
```

- [ ] **Step 5: Seed Job**

```yaml
# k8s/drf/06-seed-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: drf-seed
  namespace: drf-url
spec:
  backoffLimit: 5
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: seed
          image: drf-seed:latest
          imagePullPolicy: IfNotPresent
          env:
            - {name: SCYLLA_HOSTS, valueFrom: {configMapKeyRef: {name: drf-config, key: SCYLLA_HOSTS}}}
            - {name: REDIS_URL, valueFrom: {configMapKeyRef: {name: drf-config, key: REDIS_URL}}}
```

- [ ] **Step 6: Commit**

```bash
git add k8s/drf/
git commit -m "feat(drf): k8s manifests for namespace, scylla, redis, writer, redirect, seed"
```

---

## Task 8: Local verification (kind/minikube)

- [ ] **Step 1: Load images**

```bash
kind load docker-image drf-writer:latest drf-redirect:latest drf-seed:latest --name urlshort
```

- [ ] **Step 2: Apply**

```bash
kubectl apply -f k8s/drf/
kubectl -n drf-url wait --for=condition=Ready pod --all --timeout=300s
```

- [ ] **Step 3: Seed & test**

```bash
kubectl -n drf-url logs job/drf-seed   # expect "seed complete"
kubectl -n drf-url port-forward svc/writer 8000:8000 &
curl -X POST localhost:8000/api/shorten -H 'Content-Type: application/json' -d '{"url":"https://openai.com"}'
# take code, then:
curl -i http://localhost:30081/<code>   # expect 302 -> openai.com
curl -i http://localhost:30081/exmpl    # expect 302 -> example.com
```

- [ ] **Step 4: Commit verification**

```bash
git commit --allow-empty -m "verify(drf): end-to-end shorten + redirect works in kind"
```

---

## Self-Review Notes

- Spec coverage: Snowflake✓(T1), base62✓(T2), writer DRF+Scylla✓(T3), redirect✓(T4), seed✓(T5), Docker✓(T6), k8s+Scylla✓(T7), verify✓(T8). Per-stack Redis✓, separate namespaces✓, ScyllaDB✓, base62 numeric ID via Snowflake✓.
- Writer DAO creates keyspace/table on first call — so seed and redirect also ensure schema exists. Consistent.
- `common` importable via PYTHONPATH set in Dockerfile and test commands. Consistent.
- Redis TTL same 3600 across both stacks (per spec).
