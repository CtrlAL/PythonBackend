FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir "psycopg2-binary>=2.9" "redis>=5.0"
COPY shared/ ./shared/
COPY seed/ ./seed/
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
CMD ["python", "seed/seed.py"]
