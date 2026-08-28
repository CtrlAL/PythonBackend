FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY app/ ./app/
COPY seed/ ./seed/
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["gunicorn", "app.writer_main:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
