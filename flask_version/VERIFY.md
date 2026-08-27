# Flask URL Shortener — Verification Guide

This stack was implemented per `docs/superpowers/plans/2026-08-27-url-shortener-flask.md`.
Unit tests below were executed in this environment; the full Kubernetes end-to-end
verification requires a local cluster (kind/minikube) + Docker daemon, which was
**not available** at implementation time. Steps to verify live are included.

## Unit tests (run locally — PASSED)

```bash
# base62 util
cd flask_version/common && python -m pytest test_base62.py -v

# writer service  (uses sqlite + fakeredis shim; prod uses Postgres BIGSERIAL)
cd flask_version/writer && python -m pytest test_app.py -v

# redirect service (uses fakeredis; no real Redis needed)
cd flask_version/redirect && python -m pytest test_app.py -v
```

Notes:
- The writer unit test maps `sqlalchemy.BigInteger -> Integer` for the sqlite backend
  only. On the real Postgres deployment, `BigInteger` becomes `BIGSERIAL` and
  autoincrements correctly.
- `redis` and `fakeredis` are used so tests run without a live Redis server.

## Build images (requires Docker daemon)

```bash
docker build -f flask_version/writer/Dockerfile  -t flask-writer:latest  flask_version
docker build -f flask_version/redirect/Dockerfile -t flask-redirect:latest flask_version
docker build -f flask_version/seed/Dockerfile    -t flask-seed:latest    flask_version
```

## Deploy on kind (requires kind + Docker)

```bash
kind create cluster --name urlshort
kind load docker-image flask-writer:latest flask-redirect:latest flask-seed:latest --name urlshort
kubectl apply -f k8s/flask/
kubectl -n flask-url wait --for=condition=Ready pod --all --timeout=180s
kubectl -n flask-url logs job/flask-seed   # expect "seed complete"
```

## End-to-end test

```bash
kubectl -n flask-url port-forward svc/writer 5000:5000 &
curl -X POST localhost:5000/api/shorten -H 'Content-Type: application/json' \
  -d '{"url":"https://openai.com"}'
# -> {"code":"<code>","short_url":"http://localhost/<code>"}

curl -i http://localhost:30080/<code>        # 302 -> https://openai.com
curl -i http://localhost:30080/exmpl          # 302 -> https://example.com
```
