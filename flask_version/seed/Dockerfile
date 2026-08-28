FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir "psycopg2-binary>=2.9" "redis>=5.0"
COPY app/ ./app/
COPY seed/ ./seed/
ENV PYTHONUNBUFFERED=1
CMD ["python", "seed/seed.py"]
