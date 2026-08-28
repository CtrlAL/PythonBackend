FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir "flask>=3.0,<4.0" "psycopg2-binary>=2.9" "redis>=5.0" "pydantic>=2.0" "uvicorn>=0.20" "pytest>=8.0"
COPY app/ ./app/
COPY writer/ ./writer/
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["uvicorn", "app.writer_main:app", "--host=0.0.0.0", "--port=5000"]
