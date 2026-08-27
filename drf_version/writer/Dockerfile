FROM python:3.11-slim
WORKDIR /app
COPY writer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY writer/ ./writer/
WORKDIR /app/writer
ENV PYTHONPATH=/app/common:/app/writer
EXPOSE 8000
CMD ["gunicorn", "writerproj.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
