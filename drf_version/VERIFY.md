# DRF URL Shortener — Local Verification Guide

`kind` and a running Kubernetes cluster are NOT available in this environment, so
the end-to-end verification against a live cluster could not be executed
automatically. Use this guide to verify manually once a local cluster is up.

## Prerequisites
- Docker Desktop running (images already built locally):
  - `drf-writer:latest`, `drf-redirect:latest`, `drf-seed:latest`
- A local cluster: `kind create cluster --name urlshort` (or `minikube start`)
- `kubectl` pointing at that cluster

## Steps
1. Load images into the cluster (kind only):
   ```bash
   kind load docker-image drf-writer:latest drf-redirect:latest drf-seed:latest --name urlshort
   ```
   (For minikube, use `minikube image load drf-writer:latest drf-redirect:latest drf-seed:latest`)

2. Apply manifests:
   ```bash
   kubectl apply -f k8s/drf/
   kubectl -n drf-url wait --for=condition=Ready pod --all --timeout=300s
   ```

3. Verify seed job:
   ```bash
   kubectl -n drf-url logs job/drf-seed   # expect "seed complete"
   ```

4. Shorten a URL:
   ```bash
   kubectl -n drf-url port-forward svc/writer 8000:8000 &
   curl -X POST localhost:8000/api/shorten -H 'Content-Type: application/json' -d '{"url":"https://openai.com"}'
   # => {"code":"<CODE>","short_url":"http://localhost/<CODE>"}
   ```

5. Redirect (NodePort 30081):
   ```bash
   curl -i http://localhost:30081/<CODE>   # expect 302 -> https://openai.com
   curl -i http://localhost:30081/exmpl    # expect 302 -> https://example.com (seeded)
   ```

## Unit tests (run without a cluster)
```bash
cd drf_version/common && python -m pytest test_snowflake.py test_base62_drf.py -v
cd drf_version/writer  && PYTHONPATH=../common DJANGO_SETTINGS_MODULE=writerproj.settings python -m pytest test_views.py -v
cd drf_version/redirect && PYTHONPATH=../common DJANGO_SETTINGS_MODULE=redirectproj.settings python -m pytest test_views.py -v
```
These mock Scylla/Redis and only exercise request/response wiring.

## Notes
- ScyllaDB schema (`urlshort.links`) is created on first DAO call by writer, redirect, and seed.
- Redis key `short:<code>` has a 3600s TTL; writer warms it on create, redirect reads-through.
- The `scylla` image uses `--smp 1 --memory 1G --overprovisioned 1` for small local nodes.
