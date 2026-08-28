# fastapi_version/redirect/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
COPY app/ ./app/
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.redirect_main:app", "--host", "0.0.0.0", "--port", "8000"]
