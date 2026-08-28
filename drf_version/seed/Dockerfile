FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY shared/ ./shared/
COPY seed/ ./seed/
ENV PYTHONPATH=/app
CMD ["python", "seed/seed.py"]
