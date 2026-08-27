# fastapi_version/redirect/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY redirect/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY redirect/ ./redirect/
WORKDIR /app/redirect
ENV PYTHONPATH=/app/common
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
