FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
COPY shared/ ./shared/
COPY redirect_service/ ./redirect_service/
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["gunicorn", "redirect_service.main:application", "--bind", "0.0.0.0:8000"]
