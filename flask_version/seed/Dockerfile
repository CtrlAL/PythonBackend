FROM python:3.11-slim
WORKDIR /app
COPY seed/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY seed/seed.py ./
ENV PYTHONUNBUFFERED=1
CMD ["python", "seed.py"]
