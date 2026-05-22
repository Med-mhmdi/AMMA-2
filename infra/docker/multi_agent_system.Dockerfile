FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY ./services/multi_agent_system/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./shared /app/shared
COPY ./services/multi_agent_system /app/services/multi_agent_system
WORKDIR /app/services/multi_agent_system

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
