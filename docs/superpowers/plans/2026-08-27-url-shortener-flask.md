# URL Shortener — Flask/PostgreSQL Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read/write-split URL shortener microservice using Flask + PostgreSQL + Redis, deployable to a local Kubernetes cluster (kind/minikube) via raw YAML.

**Architecture:** Two separate Flask services — `writer` (POST /api/shorten) and `redirect` (GET /<code>). Writer generates a `BIGSERIAL` PK, encodes it to base62, persists to Postgres, and warms Redis. Redirect reads through Redis (TTL 3600s), falling back to Postgres. A seed Job populates demo links on startup. Each service has its own Docker image; all run in the `flask-url` K8s namespace.

**Tech Stack:** Python 3.11, Flask, Flask-SQLAlchemy, psycopg2-binary, redis-py, PostgreSQL 16, Redis 7, Docker, kubectl (kind/minikube).

## Global Constraints

- Short code alphabet: `0-9a-zA-Z` (62 chars), via `base62(id)`.
- Redis key `short:<code>` → `long_url`, TTL 3600s. Writer warms on create; redirect reads-through.
- Services connect to DB **directly** (no message queue).
- Deploy target: **local** kind/minikube, **raw YAML** manifests, namespace `flask-url`.
- Redis is **per-stack** (own instance in `flask-url`).
- No auth on link creation. No Helm.
- Commit frequently; each task ends with a passing test/check.

---

## Task 1: Shared base62 utility + tests

**Files:**
- Create: `flask_version/common/base62.py`
- Test: `flask_version/common/test_base62.py`

**Interfaces:**
- Produces: `encode(n: int) -> str`, `decode(s: str) -> int` (used by writer in Task 2).

- [ ] **Step 1: Write the failing tests**

```python
# flask_version/common/test_base62.py
from base62 import encode, decode

def test_encode_zero():
    assert encode(0) == "0"

def test_roundtrip():
    for n in [1, 42, 123456789, 2**31, 2**40]:
        assert decode(encode(n)) == n

def test_known_values():
    assert encode(10) == "a"
    assert encode(61) == "Z"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd flask_version/common && python -m pytest test_base62.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'base62'`)

- [ ] **Step 3: Implement**

```python
# flask_version/common/base62.py
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

- [ ] **Step 4: Run to verify pass**

Run: `cd flask_version/common && python -m pytest test_base62.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add flask_version/common/base62.py flask_version/common/test_base62.py
git commit -m "feat(flask): add base62 encode/decode util with tests"
```

---

## Task 2: Flask Writer service

**Files:**
- Create: `flask_version/writer/app.py`
- Create: `flask_version/writer/models.py`
- Create: `flask_version/writer/requirements.txt`
- Test: `flask_version/writer/test_app.py`
- (reuse `flask_version/common/base62.py` — copy into image via Dockerfile in Task 5)

**Interfaces:**
- Consumes: `encode` from `common.base62`.
- Produces: `POST /api/shorten` returning `{"code": str, "short_url": str}`; on success also writes `short:<code>` → long_url into Redis.

- [ ] **Step 1: Write failing test**

```python
# flask_version/writer/test_app.py
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
```

- [ ] **Step 2: Run to verify failure**

Run: `cd flask_version/writer && python -m pytest test_app.py -v`
Expected: FAIL (no module `app`)

- [ ] **Step 3: Implement**

```python
# flask_version/writer/requirements.txt
flask==3.0.3
flask-sqlalchemy==3.1.1
psycopg2-binary==2.9.9
redis==5.0.4
```

```python
# flask_version/writer/models.py
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Link(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    code = db.Column(db.String(16), unique=True, nullable=True)
    long_url = db.Column(db.Text, nullable=False)
```

```python
# flask_version/writer/app.py
import os
import redis
from flask import Flask, request, jsonify
from sqlalchemy.exc import IntegrityError
from models import db, Link

try:
    from common.base62 import encode
except ImportError:
    from base62 import encode

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
r = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
BASE_URL = os.environ.get("BASE_URL", "http://localhost")

@app.route("/api/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify(error="url required"), 400
    with app.app_context():
        link = Link(long_url=url)
        db.session.add(link)
        db.session.commit()
        code = encode(link.id)
        link.code = code
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify(error="could not assign code"), 500
    r.setex(f"short:{code}", 3600, url)
    return jsonify(code=code, short_url=f"{BASE_URL}/{code}"), 201

@app.route("/healthz", methods=["GET"])
def health():
    return "ok", 200
```

- [ ] **Step 4: Run to verify pass**

Run: `cd flask_version/writer && python -m pytest test_app.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add flask_version/writer/
git commit -m "feat(flask): writer service creates links and warms Redis"
```

---

## Task 3: Flask Redirect service

**Files:**
- Create: `flask_version/redirect/app.py`
- Create: `flask_version/redirect/requirements.txt`
- Test: `flask_version/redirect/test_app.py`

**Interfaces:**
- Consumes: Redis `short:<code>` (TTL 3600) and Postgres table `links(code, long_url)` (schema from writer's `Link` model; ensure table name `link` — see note).
- Produces: `GET /<code>` → HTTP 302 `Location: <long_url>`; 404 if unknown.

> Note: Flask-SQLAlchemy default table name for `Link` is `link`. Seed (Task 4) and redirect must use the same table name `link`.

- [ ] **Step 1: Write failing test**

```python
# flask_version/redirect/test_app.py
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
import redis as redislib
from app import app, get_long_url

@pytest.fixture
def client():
    r = redislib.Redis.from_url("redis://localhost:6379/0")
    r.flushdb()
    yield app.test_client()
    r.flushdb()

def test_redirect_from_redis(client):
    r = redislib.Redis.from_url("redis://localhost:6379/0")
    r.setex("short:abc", 3600, "https://example.com")
    resp = client.get("/abc")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://example.com"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd flask_version/redirect && python -m pytest test_app.py -v`
Expected: FAIL (no module `app`)

- [ ] **Step 3: Implement**

```python
# flask_version/redirect/requirements.txt
flask==3.0.3
psycopg2-binary==2.9.9
redis==5.0.4
```

```python
# flask_version/redirect/app.py
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
```

- [ ] **Step 4: Run to verify pass**

Run: `cd flask_version/redirect && python -m pytest test_app.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add flask_version/redirect/
git commit -m "feat(flask): redirect service with Redis read-through"
```

---

## Task 4: Seed script (Postgres + Redis)

**Files:**
- Create: `flask_version/seed/seed.py`
- Create: `flask_version/seed/requirements.txt`

**Interfaces:**
- Consumes: `DATABASE_URL`, `REDIS_URL` env. Writes rows into `link(code, long_url)` and `short:<code>` in Redis. Idempotent (skips existing codes).

- [ ] **Step 1: Implement seed**

```python
# flask_version/seed/requirements.txt
psycopg2-binary==2.9.9
redis==5.0.4
```

```python
# flask_version/seed/seed.py
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
```

- [ ] **Step 2: Smoke test locally (optional)**

Run with a local Postgres + Redis if available; otherwise verified in K8s Task 7.

- [ ] **Step 3: Commit**

```bash
git add flask_version/seed/
git commit -m "feat(flask): seed demo links into Postgres and Redis"
```

---

## Task 5: Dockerfiles

**Files:**
- Create: `flask_version/writer/Dockerfile`
- Create: `flask_version/redirect/Dockerfile`
- Create: `flask_version/seed/Dockerfile`
- Create: `flask_version/common/Dockerfile.common` (build context helper) — instead, copy `common/base62.py` into each service dir at build via context; simplest: each Dockerfile copies `common/base62.py` from a build context that includes both. We use a single build context `flask_version/`.

**Interfaces:** Produces images `flask-writer:latest`, `flask-redirect:latest`, `flask-seed:latest`.

- [ ] **Step 1: Writer Dockerfile**

```dockerfile
# flask_version/writer/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY writer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/base62.py ./common/base62.py
COPY writer/app.py writer/models.py ./
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python", "-m", "flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
```

- [ ] **Step 2: Redirect Dockerfile**

```dockerfile
# flask_version/redirect/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY redirect/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY redirect/app.py ./
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python", "-m", "flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
```

- [ ] **Step 3: Seed Dockerfile**

```dockerfile
# flask_version/seed/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY seed/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY seed/seed.py ./
ENV PYTHONUNBUFFERED=1
CMD ["python", "seed.py"]
```

- [ ] **Step 4: Build images**

Run (from repo root, building with context `flask_version`):
```bash
docker build -f flask_version/writer/Dockerfile -t flask-writer:latest flask_version
docker build -f flask_version/redirect/Dockerfile -t flask-redirect:latest flask_version
docker build -f flask_version/seed/Dockerfile -t flask-seed:latest flask_version
```
Expected: all three images build successfully.

- [ ] **Step 5: Commit**

```bash
git add flask_version/*/Dockerfile
git commit -m "feat(flask): Dockerfiles for writer, redirect, seed"
```

---

## Task 6: Kubernetes manifests (flask-url namespace)

**Files:**
- Create: `k8s/flask/00-namespace.yaml`
- Create: `k8s/flask/01-configmap.yaml`
- Create: `k8s/flask/02-postgres.yaml`
- Create: `k8s/flask/03-redis.yaml`
- Create: `k8s/flask/04-writer.yaml`
- Create: `k8s/flask/05-redirect.yaml`
- Create: `k8s/flask/06-seed-job.yaml`

**Interfaces:** Deploys namespace `flask-url` with Postgres, Redis, writer (ClusterIP), redirect (NodePort/Ingress), and seed Job. ConfigMap provides `DATABASE_URL` and `REDIS_URL`.

- [ ] **Step 1: Namespace + ConfigMap**

```yaml
# k8s/flask/00-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: flask-url
```

```yaml
# k8s/flask/01-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flask-config
  namespace: flask-url
data:
  DATABASE_URL: "postgresql+psycopg2://shortener:shortener@postgres:5432/shortener"
  REDIS_URL: "redis://redis:6379/0"
  BASE_URL: "http://localhost"
  DB_DSN: "postgresql://shortener:shortener@postgres:5432/shortener"
```

- [ ] **Step 2: Postgres**

```yaml
# k8s/flask/02-postgres.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: flask-url
spec:
  replicas: 1
  selector:
    matchLabels: {app: postgres}
  template:
    metadata:
      labels: {app: postgres}
    spec:
      containers:
        - name: postgres
          image: postgres:16
          env:
            - {name: POSTGRES_USER, value: "shortener"}
            - {name: POSTGRES_PASSWORD, value: "shortener"}
            - {name: POSTGRES_DB, value: "shortener"}
          ports:
            - {containerPort: 5432}
          volumeMounts:
            - {name: pgdata, mountPath: /var/lib/postgresql/data}
      volumes:
        - name: pgdata
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: flask-url
spec:
  selector: {app: postgres}
  ports:
    - {port: 5432, targetPort: 5432}
```

> NOTE: The writer must create the `link` table on startup (SQLAlchemy `db.create_all()`) or a migration init container. Add an init step in writer (Task 7 init container or a startup command). Simplest: writer runs `db.create_all()` at boot before serving. Update writer `app.py` to call `with app.app_context(): db.create_all()` in a `boot()` invoked by CMD wrapper. Provide `flask_version/writer/run.sh`:
> ```sh
> #!/bin/sh
> python -c "from app import app, db; with app.app_context(): db.create_all()"
> exec python -m flask --app app run --host=0.0.0.0 --port=5000
> ```
> and change writer Dockerfile CMD to `["sh","run.sh"]` after `COPY writer/run.sh ./`.

- [ ] **Step 3: Redis**

```yaml
# k8s/flask/03-redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: flask-url
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
  namespace: flask-url
spec:
  selector: {app: redis}
  ports:
    - {port: 6379, targetPort: 6379}
```

- [ ] **Step 4: Writer Deployment + Service**

```yaml
# k8s/flask/04-writer.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: writer
  namespace: flask-url
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
          image: flask-writer:latest
          imagePullPolicy: IfNotPresent
          envFrom:
            - configMapRef: {name: flask-config}
          ports:
            - {containerPort: 5000}
          readinessProbe:
            httpGet: {path: /healthz, port: 5000}
            initialDelaySeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: writer
  namespace: flask-url
spec:
  selector: {app: writer}
  ports:
    - {port: 5000, targetPort: 5000}
```

- [ ] **Step 5: Redirect Deployment + Service (NodePort)**

```yaml
# k8s/flask/05-redirect.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redirect
  namespace: flask-url
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
          image: flask-redirect:latest
          imagePullPolicy: IfNotPresent
          envFrom:
            - configMapRef: {name: flask-config}
          ports:
            - {containerPort: 5000}
          readinessProbe:
            httpGet: {path: /healthz, port: 5000}
            initialDelaySeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: redirect
  namespace: flask-url
spec:
  type: NodePort
  selector: {app: redirect}
  ports:
    - {port: 5000, targetPort: 5000, nodePort: 30080}
```

- [ ] **Step 6: Seed Job**

```yaml
# k8s/flask/06-seed-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: flask-seed
  namespace: flask-url
spec:
  backoffLimit: 3
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: seed
          image: flask-seed:latest
          imagePullPolicy: IfNotPresent
          env:
            - {name: DATABASE_URL, valueFrom: {configMapKeyRef: {name: flask-config, key: DB_DSN}}}
            - {name: REDIS_URL, valueFrom: {configMapKeyRef: {name: flask-config, key: REDIS_URL}}}
```

- [ ] **Step 7: Commit**

```bash
git add k8s/flask/
git commit -m "feat(flask): k8s manifests for namespace, postgres, redis, writer, redirect, seed"
```

---

## Task 7: Local verification (kind/minikube)

**Files:** none new.

- [ ] **Step 1: Start cluster & load images**

Run:
```bash
kind create cluster --name urlshort
kind load docker-image flask-writer:latest flask-redirect:latest flask-seed:latest --name urlshort
```
(or for minikube: `minikube start` then `minikube image load ...`)

- [ ] **Step 2: Apply manifests**

Run:
```bash
kubectl apply -f k8s/flask/
```
Expected: all resources Created.

- [ ] **Step 3: Wait & seed**

Run: `kubectl -n flask-url wait --for=condition=Ready pod --all --timeout=180s`
Then verify seed job: `kubectl -n flask-url logs job/flask-seed` shows "seed complete".

- [ ] **Step 4: End-to-end test**

Run (port-forward writer, then redirect via NodePort 30080):
```bash
kubectl -n flask-url port-forward svc/writer 5000:5000 &
curl -X POST localhost:5000/api/shorten -H 'Content-Type: application/json' -d '{"url":"https://openai.com"}'
```
Take returned `code`, then:
```bash
curl -i http://localhost:30080/<code>
```
Expected: `302` with `Location: https://openai.com`.
Also test a seeded code: `curl -i http://localhost:30080/exmpl` → 302 to example.com.

- [ ] **Step 5: Commit verification note**

```bash
git commit --allow-empty -m "verify(flask): end-to-end shorten + redirect works in kind"
```

---

## Self-Review Notes

- Spec coverage: base62✓ (T1), writer✓ (T2), redirect+Redis✓ (T3), seeding✓ (T4), Docker✓ (T5), k8s✓ (T6), verify✓ (T7). Per-stack Redis✓, separate namespaces✓, PostgreSQL✓, base62 numeric ID✓.
- Table name consistency: writer model `Link` → table `link`; redirect and seed query `link`. Consistent.
- Snowflake not needed for Flask (BIGSERIAL). Correct per spec.
