# URL Shortener Microservice — Design Spec

**Date:** 2026-08-27
**Status:** Approved (design)

## 1. Goal

Build a URL shortener as **two independent microservice stacks** in Python, each with
**read/write split** (separate redirect service vs. link-creation service), a **Redis
hot-link cache**, **data seeding on startup**, and **Kubernetes deployment** (local
kind/minikube via raw YAML manifests).

| Stack | Framework | Storage | Cache |
|-------|-----------|---------|-------|
| `flask-url` | Flask | PostgreSQL (SQLAlchemy) | Redis (per-stack) |
| `drf-url`   | Django + DRF | ScyllaDB (Cassandra driver) | Redis (per-stack) |

Both stacks run simultaneously in **separate K8s namespaces**.

## 2. Architecture

For each stack:

- **Writer service** (create links): `POST /api/shorten {url}` → generates a unique
  numeric ID → encodes to base62 short code → persists to DB → warms Redis → returns
  `{code, short_url}`.
- **Redirect service** (read/redirect): `GET /<code>` → check Redis → on miss read DB
  and populate Redis (TTL) → `302` redirect to long URL. 404 if unknown.
- **Redis**: per-stack cache of `short:<code>` → `long_url`, TTL 3600s. Writer warms it
  on creation; redirect reads through it.
- Services talk to the DB **directly** (no message queue). The split is purely at the
  deployment/service boundary.

## 3. Repository Layout (monorepo)

```
URLShortneer/
  flask_version/
    writer/        Dockerfile, app.py, models.py, requirements.txt
    redirect/      Dockerfile, app.py, requirements.txt
    seed/          seed.py, requirements.txt
  drf_version/
    writer/        Django project + DRF app, Dockerfile, requirements.txt
    redirect/      Lightweight Django/DRF redirect service, Dockerfile
    seed/          seed.py, requirements.txt
  k8s/
    flask/         namespace, configmap, postgres(deploy+svc), redis(deploy+svc),
                   writer(deploy+svc), redirect(deploy+svc), seed-job.yaml
    drf/           namespace, configmap, scylla(deploy+svc), redis(deploy+svc),
                   writer(deploy+svc), redirect(deploy+svc), seed-job.yaml
  docs/superpowers/specs/
```

## 4. Short-Code Generation

- Alphabet: `0-9a-zA-Z` (62 chars), function `base62(id)`.
- **Flask/Postgres:** `BIGSERIAL` primary key → `base62(id)`. Mathematically collision-free.
- **DRF/Scylla:** ScyllaDB has no auto-increment, so use a **Snowflake-style 63-bit ID
  generator** (timestamp | node-id | sequence) → `base62(id)`. Collision-free, compact,
  approximately monotonic. (Approach A, approved.)

## 5. Redis Cache

- Key: `short:<code>`, value: `long_url`, TTL 3600s.
- Redirect read path: Redis hit → redirect; miss → DB read + write to Redis.
- Writer on create: write the new mapping to Redis immediately (warm cache).

## 6. Seeding

- `seed/seed.py` is run as a **Kubernetes Job** (init/standalone) before/with the stack.
- Inserts a fixed set of demo links (e.g. `https://example.com` → `exmpl`) into the DB
  and warms Redis. Deterministic: skips already-existing codes.

## 7. Kubernetes (local kind/minikube, raw YAML)

Per stack:
- `Namespace`, `ConfigMap` (DB/Redis connection URLs), `Secret` (credentials).
- `Deployment` + `Service` (ClusterIP) for **writer** and **redirect**.
- `Deployment`/`StatefulSet` + `Service` for **Postgres** (flask) / **ScyllaDB** (drf)
  and **Redis**.
- `Job` for **seed**.
- Redirect exposed via `NodePort` or `Ingress` for local access; writer via `ClusterIP`
  (or Ingress for API testing).

No Helm — pure YAML manifests, applied per namespace.

## 8. Testing

- **Unit:** `base62` encode/decode round-trip; Snowflake uniqueness/monotonicity.
- **Integration (local):** Writer creates link → redirect returns `302` to correct URL;
  second redirect hit served from Redis (verify miss→fill→hit).
- Manual smoke via `curl` against the redirect service.

## 9. Out of Scope

- Authn/authz on link creation (public API).
- Metrics/tracing pipelines, autoscaling policies.
- Cloud-managed K8s (EKS/GKE/AKS).

## 10. Open Decisions — Resolved

| Decision | Choice |
|----------|--------|
| Flask SQL DB | PostgreSQL |
| DRF NoSQL | ScyllaDB |
| K8s target | Local kind/minikube + raw YAML |
| Scope | Both versions fully |
| Deploy split | Separate namespaces |
| Redis | Per-stack instance |
| Short code | Unique numeric ID → base62 (Snowflake for Scylla) |
