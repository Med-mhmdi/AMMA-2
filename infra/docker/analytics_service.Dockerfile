FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY ./services/analytics_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./shared /app/shared
COPY ./services/analytics_service /app/services/analytics_service
WORKDIR /app/services/analytics_service

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
