FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./services/agent_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./shared /app/shared
COPY ./services/agent_service /app/services/agent_service

WORKDIR /app/services/agent_service

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]