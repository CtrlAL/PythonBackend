# FastAPI Stack — Local Verification (manual steps)

`kind` is **not installed** in this environment, so the live Kubernetes
verification (Task 8) could not be executed automatically. Docker and `kubectl`
are present and the images `fastapi-writer:latest`, `fastapi-redirect:latest`,
and `fastapi-seed:latest` were built successfully from `fastapi_version/`.

## Prerequisites

```bash
# one-time: create a local cluster and load the images
kind create cluster --name urlshort
kind load docker-image fastapi-writer:latest fastapi-redirect:latest fastapi-seed:latest --name urlshort
```

## Apply

```bash
kubectl apply -f k8s/fastapi/
kubectl -n fastapi-url wait --for=condition=Ready pod --all --timeout=300s
```

## Verify

```bash
kubectl -n fastapi-url logs job/fastapi-seed        # expect "seed complete"
kubectl -n fastapi-url port-forward svc/writer 8000:8000 &
curl -X POST localhost:8000/api/shorten -H 'Content-Type: application/json' -d '{"url":"https://openai.com"}'
# -> {"code":"...","short_url":"http://localhost/..."}
curl -i http://localhost:30082/<code>              # expect 302 -> openai.com
curl -i http://localhost:30082/exmpl               # expect 302 -> example.com
```

## Notes

- Namespace: `fastapi-url`. ScyllaDB service `scylla:9042`, Redis `redis:6379`.
- Redirect is exposed via NodePort `30082`.
- The `conftest.py` shims in `writer/` and `redirect/` only stub `asyncore` so the
  `cassandra-driver` import succeeds on Python ≥3.12; the Docker images use
  `python:3.11-slim` where the driver works natively.
