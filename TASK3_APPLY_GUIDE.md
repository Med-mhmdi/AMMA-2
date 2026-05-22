# AMMA Task Series 3 Patch - Apply Guide

## 1. Backup first

```powershell
copy docker-compose.yml docker-compose.backup.yml
```

Or copy the whole project folder before applying the patch.

## 2. Copy patch files

Extract this ZIP into the root of your AMMA project and allow overwrite.

Important: this patch contains complete files, not fragments.

## 3. Rebuild

```powershell
docker compose down
copy .env.example .env
# If you already have a configured .env, do not overwrite it blindly. Instead compare with the new .env.example.
docker compose up --build -d
```

## 4. Pull the LLM model

```powershell
docker exec -it amma_ollama ollama pull qwen2.5:7b
```

## 5. Check containers

```powershell
docker compose ps
```

## 6. Open services

```text
Nginx entrypoint:        http://localhost
Gateway docs:           http://localhost:8000/docs
Frontend direct:        http://localhost:3000
Prometheus:             http://localhost:9090
Grafana:                http://localhost:3001    admin/admin
Loki:                   http://localhost:3100
Jaeger:                 http://localhost:16686
MinIO console:          http://localhost:9001    minio/minio123
Ollama:                 http://localhost:11434
```

## 7. Kafka topic check

```powershell
docker exec -it amma_kafka kafka-topics --bootstrap-server kafka:9092 --list
```

## 8. Logs to check

```powershell
docker compose logs -f kafka-init analytics_service notification_service expense_service loan_service gateway
```

## 9. Run load test

Install Locust locally if needed:

```powershell
pip install locust
```

Run:

```powershell
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Open:

```text
http://localhost:8089
```

## 10. Files that are still placeholders or safe to delete later

Delete only after confirming you do not need them for documentation.

### Generated junk that should not be submitted

```text
frontend/node_modules/
frontend/.venv/
services/*/.venv/
services/**/__pycache__/
```

### Placeholder files that can stay as documentation, but are not active code yet

```text
infra/k8s/**              # migration target, not fully production-ready
infra/observability/jaeger/notes.md
services/analytics_service/app/storage/snapshot_writer.py
services/notification_service/app/consumers/budget_consumer.py
services/notification_service/app/consumers/insight_consumer.py
services/auth_service/app/events/publishers.py
```

Do not delete `infra/k8s/**` if you want to show the teacher the Kubernetes migration plan.

## 11. Defense sentence

AMMA uses REST for user-facing request/response operations through the Gateway and Kafka for event-driven financial events. Expense and Loan services publish financial events, Notification and Analytics consume them, Redis accelerates analytics reads, MongoDB stores flexible AI memory, PostgreSQL stores transactional service data, MinIO is prepared for cold object storage, and Nginx provides routing plus rate limiting.
