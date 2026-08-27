# fastapi_version/seed/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY seed/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY seed/seed.py ./seed.py
ENV PYTHONPATH=/app
CMD ["python", "seed.py"]
