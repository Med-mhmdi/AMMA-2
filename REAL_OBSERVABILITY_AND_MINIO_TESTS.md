# AMMA Real Observability + MinIO Integration Tests

This patch turns the observability tools from "installed placeholders" into working integrations:

- FastAPI services expose `/metrics` in Prometheus format.
- Prometheus scrapes `/metrics`, not JSON `/health`.
- Grafana has real Prometheus + Loki data sources and a real dashboard.
- Promtail ships Docker container logs to Loki.
- OpenTelemetry sends FastAPI traces to Jaeger.
- Gateway exposes real MinIO project endpoints for receipts, reports, and analytics snapshots.

## Apply

From AMMA-2 root, copy/merge this patch into the project, then run:

```powershell
docker compose down
docker compose build --no-cache gateway auth_service expense_service loan_service analytics_service notification_service multi_agent_system
docker compose up -d
```

Wait 30-60 seconds.

## 1. Metrics test

```powershell
curl http://localhost/api/metrics
curl http://localhost:8000/metrics
```

Open:

```text
http://localhost:9090/targets
```

Expected: AMMA service targets should be UP because Prometheus now scrapes `/metrics`.

Prometheus query:

```text
up{job=~"amma_.*"}
```

## 2. Grafana dashboard test

Open:

```text
http://localhost:3001
```

Login: `admin / admin`

Go to:

```text
Dashboards -> AMMA -> AMMA Real Observability
```

Generate traffic:

```powershell
curl http://localhost/api/health
curl http://localhost/api/expenses/health
curl http://localhost/api/agent/health
```

The request-rate and target-health panels should show data.

## 3. Loki logs test

Open Grafana:

```text
Explore -> Loki
```

Query:

```logql
{compose_service="gateway"}
```

Then generate logs:

```powershell
curl http://localhost/api/health
curl http://localhost/api/expenses/health
```

Expected: gateway logs appear in Grafana Explore.

## 4. Jaeger traces test

Generate traffic:

```powershell
curl http://localhost/api/health
curl http://localhost/api/storage/minio/health
curl http://localhost/api/expenses/health
```

Open:

```text
http://localhost:16686
```

Select service:

```text
amma-gateway
amma-expense-service
amma-agent-service
```

Click **Find Traces**.

Expected: real FastAPI request traces appear.

## 5. Real MinIO project integration test

Open Swagger:

```text
http://localhost:8000/docs
```

Use these endpoints:

### Create buckets/check MinIO

```text
GET /storage/minio/health
```

### Store a receipt file in MinIO

```text
POST /storage/receipts/upload
```

Upload any receipt image or txt file. It stores the object in bucket `amma-receipts`.

### Store a generated report in MinIO

```text
POST /storage/reports/demo
```

This creates a project-related report file in `amma-reports`.

### Store analytics snapshot in MinIO

```text
POST /storage/analytics/snapshot/demo
```

This creates JSON cold-storage snapshot in `amma-analytics-snapshots`.

Then open MinIO:

```text
http://localhost:9001
```

Login from `.env`, usually:

```text
minio / minio123
```

Expected: objects are visible in the three AMMA buckets.

## Defense wording

Say:

> I corrected observability from placeholder deployment to real service instrumentation. Each FastAPI service exposes Prometheus `/metrics`, Prometheus scrapes these metrics, Grafana visualizes them, Promtail ships Docker logs into Loki, and OpenTelemetry exports traces to Jaeger. MinIO is now connected through Gateway storage endpoints for real AMMA use cases: receipt upload, exported report storage, and analytics snapshot cold storage.
