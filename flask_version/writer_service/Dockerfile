FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
COPY shared/ ./shared/
COPY writer_service/ ./writer_service/
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app
EXPOSE 5000
CMD ["uvicorn", "writer_service.main:app", "--host", "0.0.0.0", "--port", "5000"]
