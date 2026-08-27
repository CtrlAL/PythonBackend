# URL Shortener — FastAPI/ScyllaDB Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read/write-split URL shortener microservice using FastAPI + ScyllaDB (cassandra-driver) + Redis, deployable to a local Kubernetes cluster (kind/minikube) via raw YAML. This is the third independent stack, mirroring the DRF stack but on FastAPI/async.

**Architecture:** Two separate FastAPI services — `writer` (POST /api/shorten) and `redirect` (GET /<code>). Writer generates a Snowflake 63-bit ID, encodes to base62, persists to ScyllaDB, warms Redis. Redirect reads through Redis (TTL 3600s), falling back to ScyllaDB. A seed Job populates demo links. All run in the `fastapi-url` K8s namespace.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, cassandra-driver, redis-py, ScyllaDB 5, Redis 7, Docker, kubectl (kind/minikube).

## Global Constraints

- Short code: unique 63-bit Snowflake ID → `base62(id)`, alphabet `0-9a-zA-Z` (62 chars).
- Redis key `short:<code>` → `long_url`, TTL 3600s. Writer warms on create; redirect reads-through.
- Services connect to ScyllaDB **directly** (no queue). Keyspace `urlshort`, table `links(code text PRIMARY KEY, long_url text)`.
- Deploy target: **local** kind/minikube, **raw YAML**, namespace `fastapi-url`.
- Redis **per-stack** (own instance in `fastapi-url`).
- No auth on link creation. No Helm.

---

## Task 1: Snowflake generator + base62 (shared)

**Files:**
- Create: `fastapi_version/common/snowflake.py`
- Create: `fastapi_version/common/base62.py`
- Test: `fastapi_version/common/test_utils.py`

**Interfaces:**
- Produces: `Snowflake.next_id() -> int`, `encode(n) -> str`, `decode(s) -> int`.

- [ ] **Step 1: Write tests**

```python
# fastapi_version/common/test_utils.py
import threading
from snowflake import Snowflake
from base62 import encode, decode

def test_snowflake_unique_monotonic():
    s = Snowflake(node_id=1)
    ids = [s.next_id() for _ in range(10000)]
    assert len(ids) == len(set(ids))
    assert ids == sorted(ids)

def test_snowflake_threads():
    s = Snowflake(node_id=3)
    out = []
    def w():
        for _ in range(2000): out.append(s.next_id())
    ts = [threading.Thread(target=w) for _ in range(4)]
    for t in ts: t.start()
    for t in ts: t.join()
    assert len(out) == len(set(out))

def test_base62_roundtrip():
    for n in [0, 1, 42, 2**40, 2**62]:
        assert decode(encode(n)) == n
```

- [ ] **Step 2: Implement**

```python
# fastapi_version/common/snowflake.py
import time, threading
EPOCH_MS = 1288834974657
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

```python
# fastapi_version/common/base62.py
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)
def encode(n):
    if n == 0: return ALPHABET[0]
    s = ""
    while n > 0:
        s += ALPHABET[n % BASE]; n //= BASE
    return s[::-1]
def decode(s):
    n = 0
    for c in s: n = n * BASE + ALPHABET.index(c)
    return n
```

- [ ] **Step 3: Run & commit**

Run: `cd fastapi_version/common && python -m pytest test_utils.py -v` → PASS
```bash
git add fastapi_version/common/ && git commit -m "feat(fastapi): snowflake + base62 utils with tests"
```

---

## Task 2: DAL module (ScyllaDB)

**Files:**
- Create: `fastapi_version/common/dal.py`

**Interfaces:**
- Consumes: `SCYLLA_HOSTS` env.
- Produces: `init_db()`, `insert_link(code, long_url)`, `get_long_url(code)`.

- [ ] **Step 1: Implement**

```python
# fastapi_version/common/dal.py
import os, cassandra.cluster
from cassandra.query import dict_factory
_session = None
def get_session():
    global _session
    if _session is None:
        hosts = os.environ.get("SCYLLA_HOSTS", "127.0.0.1").split(",")
        cl = cassandra.cluster.Cluster(hosts)
        _session = cl.connect()
        _session.row_factory = dict_factory
        _session.execute("CREATE KEYSPACE IF NOT EXISTS urlshort WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
        _session.set_keyspace("urlshort")
        _session.execute("CREATE TABLE IF NOT EXISTS links (code text PRIMARY KEY, long_url text)")
    return _session
def init_db():
    get_session()
def insert_link(code, long_url):
    get_session().execute("INSERT INTO links (code, long_url) VALUES (%s, %s)", (code, long_url))
def get_long_url(code):
    row = get_session().execute("SELECT long_url FROM links WHERE code=%s", (code,)).one()
    return row["long_url"] if row else None
```

- [ ] **Step 2: Commit**

```bash
git add fastapi_version/common/dal.py && git commit -m "feat(fastapi): ScyllaDB DAL"
```

---

## Task 3: Writer service (FastAPI)

**Files:**
- Create: `fastapi_version/writer/main.py`
- Create: `fastapi_version/writer/requirements.txt`
- Test: `fastapi_version/writer/test_main.py`

**Interfaces:**
- Consumes: `Snowflake`, `encode`, `dal.insert_link`, Redis.
- Produces: `POST /api/shorten` → `{"code": str, "short_url": str}`; warms `short:<code>`.

- [ ] **Step 1: Write test**

```python
# fastapi_version/writer/test_main.py
import os
os.environ.setdefault("SCYLLA_HOSTS", "127.0.0.1")
from fastapi.testclient import TestClient
from main import app
def test_shorten(monkeypatch):
    import dal
    monkeypatch.setattr(dal, "insert_link", lambda c, u: None)
    c = TestClient(app)
    r = c.post("/api/shorten", json={"url": "https://example.com"})
    assert r.status_code == 201
    assert r.json()["code"]
```

- [ ] **Step 2: Implement**

```python
# fastapi_version/writer/requirements.txt
fastapi==0.111.0
uvicorn==0.30.1
cassandra-driver==3.29.1
redis==5.0.4
pydantic==2.7.1
```

```python
# fastapi_version/writer/main.py
import os, redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from common.snowflake import Snowflake
from common.base62 import encode
from common import dal

app = FastAPI()
_redis = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
_sf = Snowflake(node_id=int(os.environ.get("NODE_ID", "1")))
_BASE = os.environ.get("BASE_URL", "http://localhost")

class Req(BaseModel):
    url: HttpUrl

@app.on_event("startup")
def startup():
    dal.init_db()

@app.post("/api/shorten", status_code=201)
def shorten(body: Req):
    code = encode(_sf.next_id())
    dal.insert_link(code, str(body.url))
    _redis.setex(f"short:{code}", 3600, str(body.url))
    return {"code": code, "short_url": f"{_BASE}/{code}"}

@app.get("/healthz")
def health():
    return {"status": "ok"}
```

- [ ] **Step 3: Run & commit**

Run: `cd fastapi_version/writer && PYTHONPATH=../common python -m pytest test_main.py -v` → PASS
```bash
git add fastapi_version/writer/ && git commit -m "feat(fastapi): writer service"
```

---

## Task 4: Redirect service (FastAPI)

**Files:**
- Create: `fastapi_version/redirect/main.py`
- Create: `fastapi_version/redirect/requirements.txt`
- Test: `fastapi_version/redirect/test_main.py`

**Interfaces:**
- Consumes: `dal.get_long_url`, Redis `short:<code>`.
- Produces: `GET /<code>` → 302 redirect; 404 if unknown.

- [ ] **Step 1: Write test**

```python
# fastapi_version/redirect/test_main.py
import os
os.environ.setdefault("SCYLLA_HOSTS", "127.0.0.1")
from fastapi.testclient import TestClient
from main import app
def test_redirect(monkeypatch):
    import dal
    monkeypatch.setattr(dal, "get_long_url", lambda code: "https://example.com")
    c = TestClient(app)
    r = c.get("/abc")
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com"
```

- [ ] **Step 2: Implement**

```python
# fastapi_version/redirect/requirements.txt
fastapi==0.111.0
uvicorn==0.30.1
cassandra-driver==3.29.1
redis==5.0.4
```

```python
# fastapi_version/redirect/main.py
import os, redis
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi import HTTPException
from common import dal

app = FastAPI()
_redis = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))

@app.on_event("startup")
def startup():
    dal.init_db()

@app.get("/{code}")
def redir(code: str):
    cached = _redis.get(f"short:{code}")
    if cached:
        return RedirectResponse(cached.decode(), status_code=302)
    url = dal.get_long_url(code)
    if not url:
        raise HTTPException(status_code=404, detail="not found")
    _redis.setex(f"short:{code}", 3600, url)
    return RedirectResponse(url, status_code=302)

@app.get("/healthz")
def health():
    return {"status": "ok"}
```

- [ ] **Step 3: Run & commit**

Run: `cd fastapi_version/redirect && PYTHONPATH=../common python -m pytest test_main.py -v` → PASS
```bash
git add fastapi_version/redirect/ && git commit -m "feat(fastapi): redirect service"
```

---

## Task 5: Seed script

**Files:**
- Create: `fastapi_version/seed/seed.py`
- Create: `fastapi_version/seed/requirements.txt`

- [ ] **Step 1: Implement**

```python
# fastapi_version/seed/requirements.txt
cassandra-driver==3.29.1
redis==5.0.4
```

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add fastapi_version/seed/ && git commit -m "feat(fastapi): seed demo links"
```

---

## Task 6: Dockerfiles

**Files:**
- Create: `fastapi_version/writer/Dockerfile`
- Create: `fastapi_version/redirect/Dockerfile`
- Create: `fastapi_version/seed/Dockerfile`

- [ ] **Step 1: Writer**

```dockerfile
# fastapi_version/writer/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY writer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY writer/ ./writer/
WORKDIR /app/writer
ENV PYTHONPATH=/app/common
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Redirect**

```dockerfile
# fastapi_version/redirect/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY redirect/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY redirect/ ./redirect/
WORKDIR /app/redirect
ENV PYTHONPATH=/app/common
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Seed**

```dockerfile
# fastapi_version/seed/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY seed/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY seed/seed.py ./seed.py
ENV PYTHONPATH=/app/common
CMD ["python", "seed.py"]
```

- [ ] **Step 4: Build & commit**

```bash
docker build -f fastapi_version/writer/Dockerfile -t fastapi-writer:latest fastapi_version
docker build -f fastapi_version/redirect/Dockerfile -t fastapi-redirect:latest fastapi_version
docker build -f fastapi_version/seed/Dockerfile -t fastapi-seed:latest fastapi_version
```
```bash
git add fastapi_version/*/Dockerfile && git commit -m "feat(fastapi): Dockerfiles"
```

---

## Task 7: Kubernetes manifests (fastapi-url namespace)

**Files:**
- Create: `k8s/fastapi/00-namespace.yaml`
- Create: `k8s/fastapi/01-configmap.yaml`
- Create: `k8s/fastapi/02-scylla.yaml`
- Create: `k8s/fastapi/03-redis.yaml`
- Create: `k8s/fastapi/04-writer.yaml`
- Create: `k8s/fastapi/05-redirect.yaml`
- Create: `k8s/fastapi/06-seed-job.yaml`

- [ ] **Step 1: Namespace + ConfigMap**

```yaml
# k8s/fastapi/00-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: fastapi-url
```
```yaml
# k8s/fastapi/01-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fastapi-config
  namespace: fastapi-url
data:
  SCYLLA_HOSTS: "scylla"
  REDIS_URL: "redis://redis:6379/0"
  BASE_URL: "http://localhost"
```

- [ ] **Step 2: ScyllaDB + Redis** (same as DRF plan Task 7 steps 2-3, substituting namespace `fastapi-url`, name `fastapi-config`)

- [ ] **Step 3: Writer + Redirect**

```yaml
# k8s/fastapi/04-writer.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: writer
  namespace: fastapi-url
spec:
  replicas: 1
  selector: {matchLabels: {app: writer}}
  template:
    metadata: {labels: {app: writer}}
    spec:
      containers:
        - name: writer
          image: fastapi-writer:latest
          imagePullPolicy: IfNotPresent
          envFrom: [{configMapRef: {name: fastapi-config}}]
          ports: [{containerPort: 8000}]
          readinessProbe:
            httpGet: {path: /healthz, port: 8000}
            initialDelaySeconds: 10
---
apiVersion: v1
kind: Service
metadata: {name: writer, namespace: fastapi-url}
spec:
  selector: {app: writer}
  ports: [{port: 8000, targetPort: 8000}]
```

```yaml
# k8s/fastapi/05-redirect.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redirect
  namespace: fastapi-url
spec:
  replicas: 1
  selector: {matchLabels: {app: redirect}}
  template:
    metadata: {labels: {app: redirect}}
    spec:
      containers:
        - name: redirect
          image: fastapi-redirect:latest
          imagePullPolicy: IfNotPresent
          envFrom: [{configMapRef: {name: fastapi-config}}]
          ports: [{containerPort: 8000}]
          readinessProbe:
            httpGet: {path: /healthz, port: 8000}
            initialDelaySeconds: 10
---
apiVersion: v1
kind: Service
metadata: {name: redirect, namespace: fastapi-url}
spec:
  type: NodePort
  selector: {app: redirect}
  ports: [{port: 8000, targetPort: 8000, nodePort: 30082}]
```

- [ ] **Step 4: Seed Job**

```yaml
# k8s/fastapi/06-seed-job.yaml
apiVersion: batch/v1
kind: Job
metadata: {name: fastapi-seed, namespace: fastapi-url}
spec:
  backoffLimit: 5
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: seed
          image: fastapi-seed:latest
          imagePullPolicy: IfNotPresent
          env:
            - {name: SCYLLA_HOSTS, valueFrom: {configMapKeyRef: {name: fastapi-config, key: SCYLLA_HOSTS}}}
            - {name: REDIS_URL, valueFrom: {configMapKeyRef: {name: fastapi-config, key: REDIS_URL}}}
```

- [ ] **Step 5: Commit**

```bash
git add k8s/fastapi/ && git commit -m "feat(fastapi): k8s manifests"
```

---

## Task 8: Local verification

- [ ] **Step 1: Load + apply**

```bash
kind load docker-image fastapi-writer:latest fastapi-redirect:latest fastapi-seed:latest --name urlshort
kubectl apply -f k8s/fastapi/
kubectl -n fastapi-url wait --for=condition=Ready pod --all --timeout=300s
```

- [ ] **Step 2: Test**

```bash
kubectl -n fastapi-url logs job/fastapi-seed
kubectl -n fastapi-url port-forward svc/writer 8000:8000 &
curl -X POST localhost:8000/api/shorten -H 'Content-Type: application/json' -d '{"url":"https://openai.com"}'
curl -i http://localhost:30082/<code>   # 302 -> openai.com
curl -i http://localhost:30082/exmpl    # 302 -> example.com
```

- [ ] **Step 3: Commit**

```bash
git commit --allow-empty -m "verify(fastapi): end-to-end works in kind"
```

---

## Self-Review Notes

- Spec coverage: Snowflake+base62✓(T1), DAL✓(T2), writer✓(T3), redirect✓(T4), seed✓(T5), Docker✓(T6), k8s+Scylla✓(T7), verify✓(T8). Per-stack Redis✓, namespace `fastapi-url`✓, ScyllaDB✓, base62 via Snowflake✓.
- Matches DRF storage choice (ScyllaDB); differs by framework (FastAPI vs Django/DRF).
- `common` importable via PYTHONPATH set in Dockerfile + test commands.
