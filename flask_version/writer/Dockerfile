FROM python:3.11-slim
WORKDIR /app
COPY writer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/base62.py ./common/base62.py
COPY writer/app.py writer/models.py ./
COPY writer/run.sh ./
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["sh", "run.sh"]
