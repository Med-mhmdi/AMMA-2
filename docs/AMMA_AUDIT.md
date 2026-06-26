# AMMA Technical Audit

Date: 2026-06-26

## Executive Summary

AMMA is currently a strong academic/demo monorepo for a microservice-based personal finance platform. It contains real FastAPI services, Docker Compose orchestration, Kubernetes/Helm/ArgoCD/Istio materials, observability manifests, eventing, AI-agent code, and a Vite React frontend.

For AMMA Real v1, the repository should be narrowed into a smaller deployable product before any VPS production launch. The first real product should focus on auth, expenses, budgets, loans, basic analytics, a gateway, one relational database, Redis only if needed, and a rebuilt frontend. AI, Kubernetes, Istio, ArgoCD, MinIO, Kafka, and heavy monitoring should be disabled or postponed until the core finance workflows are stable.

## 1. Project Structure Summary

Top-level structure:

| Path | Purpose | Status |
|---|---|---|
| `.github/workflows/` | CI workflow for Kaniko image builds and optional ArgoCD sync | Academic/platform-oriented, not VPS-ready |
| `docs/` | Architecture reports, diagrams, platform notes, task reports | Useful, but mixed with academic deliverables |
| `frontend/` | Current React + Vite frontend | Exists, but should be rebuilt for product v1 |
| `infra/` | Dockerfiles, Nginx, Redis, Kafka, K8s, Helm, ArgoCD, Istio, observability, Terraform, Ansible | Broad platform lab; too heavy for v1 |
| `scripts/task3/` | PowerShell scripts for k3d, Istio, ArgoCD, registry, traffic, validation | Academic/local platform scripts |
| `services/` | Backend microservices | Main business logic |
| `shared/` | Shared Python packages for config, DB, events, schemas, clients, storage, observability | Useful, but creates coupling |
| `tests/load/` | Locust load test scripts | Useful later; not enough for release quality |
| Root YAML/JSON files | Kubernetes patches, observability manifests, platform experiments | Should be moved/archive-documented later |
| `docker-compose.yml` | Main local development stack | Main runnable orchestration file |
| `.env.example` | Development environment template | Useful, but contains insecure defaults |
| `.env` | Local environment file | Should not be used as production source |
| `Makefile` | Empty | Should be filled or removed later |

Important service structure:

| Path | Purpose |
|---|---|
| `services/gateway/` | API gateway and reverse proxy routes |
| `services/auth_service/` | User registration, login, JWT generation |
| `services/expense_service/` | Expenses, categories, budgets |
| `services/loan_service/` | Loans and loan status tracking |
| `services/analytics_service/` | Dashboard, category, daily, forecast, cache invalidation |
| `services/notification_service/` | Notification CRUD/status and event consumers |
| `services/multi_agent_system/` | AI assistant, agents, LangGraph-style workflow, memory, LLM provider |

Important infrastructure structure:

| Path | Purpose |
|---|---|
| `infra/docker/` | Dockerfiles for backend services and frontend |
| `infra/nginx/` | Reverse proxy config for frontend and gateway |
| `infra/redis/` | Redis config |
| `infra/kafka/` | Topic documentation and topic init script |
| `infra/k8s/` | Raw Kubernetes manifests |
| `infra/helm/` | Helm charts for app services |
| `infra/argocd/` | ArgoCD app-of-apps and service applications |
| `infra/istio/` | Istio gateway, virtual service, destination rules, rate limiting |
| `infra/observability/` | Prometheus, Grafana, Loki, Promtail, Jaeger, OpenTelemetry materials |
| `infra/terraform/cluster/` | Terraform cluster files, including committed local state files |
| `infra/ansible/` | Strimzi Kafka deployment playbook/role |

## 2. Detected Services and Purpose

### Application Services

| Service | Path | Runtime | Purpose | v1 Recommendation |
|---|---|---|---|---|
| Gateway | `services/gateway` | FastAPI/Uvicorn | Single public API entrypoint; proxies auth, expenses, loans, analytics, notifications, agent, and MinIO routes | Keep |
| Auth Service | `services/auth_service` | FastAPI/Uvicorn | Register/login users and issue JWT tokens | Keep |
| Expense Service | `services/expense_service` | FastAPI/Uvicorn | CRUD expenses, categories, budgets, summaries | Keep |
| Loan Service | `services/loan_service` | FastAPI/Uvicorn | CRUD loans and repayment/status tracking | Keep if loans are core to v1 |
| Analytics Service | `services/analytics_service` | FastAPI/Uvicorn | Dashboard summaries, categories, daily data, forecasts, Redis cache | Keep as simple read-side service or merge later |
| Notification Service | `services/notification_service` | FastAPI/Uvicorn | Notification records and status updates; consumers for finance events | Postpone unless v1 needs in-app notifications |
| Multi-Agent System | `services/multi_agent_system` | FastAPI/Uvicorn | AI assistant, multi-agent workflow, LLM calls, MongoDB memory, Langfuse tracing | Disable/postpone for v1 |
| Frontend | `frontend` | React + Vite dev server | Current web UI for auth, dashboard, expenses, loans, analytics, AI assistant | Rebuild |
| Nginx | `infra/nginx` | Nginx | Routes `/api/` to gateway and `/` to frontend | Keep for VPS reverse proxy, but harden |

### Supporting Runtime Services

| Service | Purpose | v1 Recommendation |
|---|---|---|
| PostgreSQL `auth_db` | Auth data | Keep, preferably consolidate DB strategy |
| PostgreSQL `expense_db` | Expense/category/budget data | Keep |
| PostgreSQL `loan_db` | Loan data | Keep if loans stay in v1 |
| PostgreSQL `notification_db` | Notification data | Postpone with notification service |
| MongoDB | AI memory storage | Disable/postpone |
| Redis | Analytics cache | Optional for v1; keep only if measured benefit |
| Kafka + Zookeeper | Event backbone for analytics, notifications, audit, AI insights | Disable/postpone for v1 |
| Kafka init | Creates AMMA topics and DLQs | Disable with Kafka |
| MinIO | Object storage for receipts/reports/snapshots | Postpone unless receipt upload is a v1 feature |
| Ollama | Local LLM runtime | Disable/postpone |
| Prometheus | Metrics | Postpone heavy monitoring; use basic logs/health first |
| Grafana | Dashboards | Postpone heavy monitoring |
| Loki | Log aggregation | Postpone heavy monitoring |
| Promtail | Docker log shipper | Postpone heavy monitoring |
| Jaeger | Tracing/OTLP endpoint | Postpone heavy monitoring |

## 3. Docker Compose Files and Service Commands

Detected Compose file:

| File | Purpose |
|---|---|
| `docker-compose.yml` | Main local development stack for app, datastores, AI, Nginx, and observability |

No separate production Compose file was detected.

Compose services:

| Compose Service | Image/Build | Command or Runtime | Exposed Host Ports |
|---|---|---|---|
| `auth_db` | `postgres:16` | PostgreSQL | `5433 -> 5432` |
| `expense_db` | `postgres:16` | PostgreSQL | `5434 -> 5432` |
| `loan_db` | `postgres:16` | PostgreSQL | `5435 -> 5432` |
| `notification_db` | `postgres:16` | PostgreSQL | `5436 -> 5432` |
| `mongodb` | `mongo:7` | MongoDB | `27017 -> 27017` |
| `redis` | `redis:7` | `redis-server /usr/local/etc/redis/redis.conf` | `6379 -> 6379` |
| `zookeeper` | `confluentinc/cp-zookeeper:7.5.0` | Zookeeper | `22181 -> 2181` |
| `kafka` | `confluentinc/cp-kafka:7.5.0` | Kafka broker | `29092 -> 29092` |
| `kafka-init` | `confluentinc/cp-kafka:7.5.0` | `bash /init-topics.sh` | None |
| `minio` | `minio/minio:latest` | `server /data --console-address ":9001"` | `9000`, `9001` |
| `auth_service` | `infra/docker/auth_service.Dockerfile` | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Internal only |
| `expense_service` | `infra/docker/expense_service.Dockerfile` | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Internal only |
| `loan_service` | `infra/docker/loan_service.Dockerfile` | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Internal only |
| `analytics_service` | `infra/docker/analytics_service.Dockerfile` | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Internal only |
| `notification_service` | `infra/docker/notification_service.Dockerfile` | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Internal only |
| `ollama` | `ollama/ollama:latest` | Ollama server | `11434 -> 11434` |
| `multi_agent_system` | `infra/docker/multi_agent_system.Dockerfile` | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | `8005 -> 8000` |
| `gateway` | `infra/docker/gateway.Dockerfile` | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | `8000 -> 8000` |
| `frontend` | `infra/docker/frontend.Dockerfile` | `npm run dev -- --host 0.0.0.0 --port 3000` | `3000 -> 3000` |
| `nginx` | `nginx:1.27-alpine` | Nginx reverse proxy | `80 -> 80` |
| `prometheus` | `prom/prometheus:v2.55.0` | Prometheus with local config | `9090 -> 9090` |
| `grafana` | `grafana/grafana:11.2.0` | Grafana | `3001 -> 3000` |
| `loki` | `grafana/loki:3.2.1` | Loki | `3100 -> 3100` |
| `promtail` | `grafana/promtail:3.2.1` | Promtail with Docker socket mount | None |
| `jaeger` | `jaegertracing/all-in-one:1.60` | Jaeger all-in-one with OTLP | `16686`, `4317`, `4318` |

Compose concern: the frontend container runs the Vite dev server, not a production static build. For VPS production, this should become a Next.js production server or static build behind Nginx/Caddy/Traefik.

## 4. Required Environment Variables by Service

The repository uses `.env.example`, direct `os.getenv(...)` calls, and Compose interpolation. Values below are variable names, not production-safe values.

### Global

| Variable | Used By |
|---|---|
| `APP_ENV` | All Python services/observability |
| `APP_DEBUG` | Gateway/K8s config |
| `APP_HOST` | Environment template |
| `OTEL_TRACES_ENABLED` | Services via shared observability |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Services via shared observability |

### Gateway

| Variable | Purpose |
|---|---|
| `APP_NAME` | Gateway title/name override |
| `APP_ENV` | Environment |
| `APP_DEBUG` | Debug flag |
| `AUTH_SERVICE_URL` | Auth upstream |
| `EXPENSE_SERVICE_URL` | Expense upstream |
| `LOAN_SERVICE_URL` | Loan upstream |
| `ANALYTICS_SERVICE_URL` | Analytics upstream |
| `NOTIFICATION_SERVICE_URL` | Notification upstream |
| `AGENT_SERVICE_URL` | AI agent upstream |
| `MINIO_ENDPOINT` | MinIO endpoint for storage proxy |
| `MINIO_ROOT_USER` | MinIO access key |
| `MINIO_ROOT_PASSWORD` | MinIO secret key |
| `MINIO_SECURE` | Whether MinIO uses TLS |

### Auth Service

| Variable | Purpose |
|---|---|
| `APP_ENV` | Environment |
| `AUTH_DATABASE_URL` | PostgreSQL SQLAlchemy connection URL |
| `JWT_SECRET_KEY` | JWT signing secret |
| `JWT_ALGORITHM` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `AUTH_DB_NAME`, `AUTH_DB_USER`, `AUTH_DB_PASSWORD`, `AUTH_DB_HOST`, `AUTH_DB_PORT` | Compose DB setup/template variables |

### Expense Service

| Variable | Purpose |
|---|---|
| `APP_ENV` | Environment |
| `EXPENSE_DATABASE_URL` | PostgreSQL SQLAlchemy connection URL |
| `JWT_SECRET_KEY` | JWT validation secret |
| `JWT_ALGORITHM` | JWT algorithm |
| `KAFKA_BOOTSTRAP_SERVERS` | Event producer/consumer bootstrap |
| `KAFKA_CLIENT_ID` | Event client ID |
| `EXPENSE_DB_NAME`, `EXPENSE_DB_USER`, `EXPENSE_DB_PASSWORD`, `EXPENSE_DB_HOST`, `EXPENSE_DB_PORT` | Compose DB setup/template variables |

### Loan Service

| Variable | Purpose |
|---|---|
| `APP_ENV` | Environment |
| `LOAN_DATABASE_URL` | PostgreSQL SQLAlchemy connection URL |
| `JWT_SECRET_KEY` | JWT validation secret |
| `JWT_ALGORITHM` | JWT algorithm |
| `KAFKA_BOOTSTRAP_SERVERS` | Event producer/consumer bootstrap |
| `KAFKA_CLIENT_ID` | Event client ID |
| `LOAN_DB_NAME`, `LOAN_DB_USER`, `LOAN_DB_PASSWORD`, `LOAN_DB_HOST`, `LOAN_DB_PORT` | Compose DB setup/template variables |

### Analytics Service

| Variable | Purpose |
|---|---|
| `APP_ENV` | Environment |
| `EXPENSE_SERVICE_URL` | Expense upstream |
| `LOAN_SERVICE_URL` | Loan upstream |
| `REDIS_URL` | Cache backend |
| `JWT_SECRET_KEY` | JWT validation secret |
| `JWT_ALGORITHM` | JWT algorithm |
| `KAFKA_BOOTSTRAP_SERVERS` | Event consumer bootstrap where used |
| `KAFKA_CLIENT_ID` | Event client ID |

### Notification Service

| Variable | Purpose |
|---|---|
| `APP_ENV` | Environment |
| `NOTIFICATION_DATABASE_URL` | PostgreSQL SQLAlchemy connection URL |
| `JWT_SECRET_KEY` | JWT validation secret |
| `JWT_ALGORITHM` | JWT algorithm |
| `KAFKA_BOOTSTRAP_SERVERS` | Event consumer/producer bootstrap |
| `KAFKA_CLIENT_ID` | Event client ID |
| `NOTIFICATION_DB_NAME`, `NOTIFICATION_DB_USER`, `NOTIFICATION_DB_PASSWORD`, `NOTIFICATION_DB_HOST`, `NOTIFICATION_DB_PORT` | Compose DB setup/template variables |

### Multi-Agent System

| Variable | Purpose |
|---|---|
| `OLLAMA_BASE_URL` | Ollama endpoint |
| `OLLAMA_MODEL` | Text model |
| `OLLAMA_VISION_MODEL` | Vision model |
| `MONGODB_URL` | Agent memory database URL |
| `MONGODB_DB_NAME` | Agent memory database name |
| `AUTH_SERVICE_URL` | Auth tool/upstream |
| `EXPENSE_SERVICE_URL` | Expense tool/upstream |
| `LOAN_SERVICE_URL` | Loan tool/upstream |
| `ANALYTICS_SERVICE_URL` | Analytics tool/upstream |
| `NOTIFICATION_SERVICE_URL` | Notification tool/upstream |
| `LANGFUSE_ENABLED` | Enables LLM tracing |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key |
| `LANGFUSE_HOST` | Langfuse endpoint |
| `LANGFUSE_ENVIRONMENT` | Langfuse environment label |
| `LANGFUSE_RELEASE` | Langfuse release label |
| `LANGFUSE_CAPTURE_INPUT_OUTPUT` | Whether to store prompts/responses |
| `LANGFUSE_MAX_PAYLOAD_CHARS` | Prompt/response truncation |
| `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT` | Present in Compose/env template, not clearly wired in service config |

### Frontend

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | API base URL for current Vite frontend |
| `FRONTEND_PORT` | Template/development port |

### Datastores and Infra

| Component | Variables |
|---|---|
| PostgreSQL Compose databases | `*_DB_NAME`, `*_DB_USER`, `*_DB_PASSWORD` |
| Redis | `REDIS_HOST`, `REDIS_PORT`, `REDIS_URL` |
| Kafka | `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_CLIENT_ID`, plus broker-local `KAFKA_*` settings |
| Kafka init | `KAFKA_PARTITIONS`, `KAFKA_REPLICATION_FACTOR` optional defaults |
| MinIO | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_ENDPOINT`, `MINIO_PUBLIC_ENDPOINT`, `MINIO_API_PORT`, `MINIO_CONSOLE_PORT`, `MINIO_SECURE` |
| MongoDB | `MONGODB_URL`, `MONGODB_DB_NAME` |
| Ollama | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_VISION_MODEL` |
| Observability | `PROMETHEUS_PORT`, `GRAFANA_PORT`, `LOKI_PORT`, `JAEGER_UI_PORT`, `OTEL_*` |

## 5. Exposed Ports and Possible Conflicts

| Host Port | Service | Risk |
|---|---|---|
| `80` | Nginx | Conflicts with any local/prod web server; must be the only public HTTP entrypoint |
| `3000` | Frontend Vite dev server | Common conflict with React/Next.js dev servers; not suitable as public prod port |
| `3001` | Grafana | Common local dev conflict |
| `5433` | Auth PostgreSQL | Usually okay, but four separate Postgres host ports add noise |
| `5434` | Expense PostgreSQL | Same |
| `5435` | Loan PostgreSQL | Same |
| `5436` | Notification PostgreSQL | Same |
| `6379` | Redis | Common conflict with local Redis |
| `8000` | Gateway | Common conflict with local APIs |
| `8005` | Multi-agent service | Exposes AI service directly, should not be public in prod |
| `9000` | MinIO API | Common conflict; should not be public unless explicitly secured |
| `9001` | MinIO Console | Should not be public in prod |
| `9090` | Prometheus | Should not be public in prod |
| `16686` | Jaeger UI | Should not be public in prod |
| `4317` | OTLP gRPC | Should not be public in prod |
| `4318` | OTLP HTTP | Should not be public in prod |
| `27017` | MongoDB | Should never be public |
| `29092` | Kafka external listener | Should never be public for v1 |
| `22181` | Zookeeper | Should never be public |
| `3100` | Loki | Should not be public |
| `11434` | Ollama | Should not be public |

Recommendation for VPS v1: expose only `80` and `443` publicly. Everything else should be internal Docker network only. Use one public reverse proxy route to the frontend and API.

## 6. Databases and Storage Dependencies

### Current Storage Layout

| Dependency | Current Use | Persistence |
|---|---|---|
| PostgreSQL `auth_db` | Users/auth | Docker volume `auth_db_data` |
| PostgreSQL `expense_db` | Expenses, categories, budgets | Docker volume `expense_db_data` |
| PostgreSQL `loan_db` | Loans | Docker volume `loan_db_data` |
| PostgreSQL `notification_db` | Notifications | Docker volume `notification_db_data` |
| MongoDB | Agent memory | Docker volume `mongodb_data` |
| Redis | Analytics cache | Docker volume `redis_data` |
| Kafka/Zookeeper | Event log and coordination | No explicit Kafka/Zookeeper named volumes in Compose |
| MinIO | Receipts, reports, analytics snapshots | Docker volume `minio_data` |
| Ollama | Local model files | Docker volume `ollama_data` |
| Prometheus | Metrics TSDB | Docker volume `prometheus_data` |
| Grafana | Dashboards/state | Docker volume `grafana_data` |
| Loki | Logs | Docker volume `loki_data` |

### Database Concerns

1. Four separate PostgreSQL containers are overkill for a first VPS product. Use one PostgreSQL instance with separate databases/schemas, or one database with service-owned schemas.
2. Kubernetes config maps point all service database URLs at the same `amma_db`, while Compose uses separate databases. This mismatch will create migration and ownership confusion.
3. No migration framework is visible in the audit path. Production needs Alembic or equivalent migration discipline before deployment.
4. Default credentials are development-only and appear in examples/manifests.
5. Terraform state files are present under `infra/terraform/cluster/`; state files should not be committed for real infrastructure.

## 7. Essential Services for AMMA Real v1

AMMA Real v1 should prioritize the smallest useful product:

| Keep for v1 | Why |
|---|---|
| Frontend, rebuilt | Users need a polished product surface |
| Gateway | Keeps public API stable and hides internal services |
| Auth Service | Required for real user accounts |
| Expense Service | Core financial tracking feature |
| Loan Service | Keep if loans are a core AMMA differentiator; otherwise postpone |
| Analytics Service | Keep as simple summaries/forecasting, but avoid overengineering |
| PostgreSQL | Core durable transactional storage |
| Nginx or other reverse proxy | Public HTTP/HTTPS routing |

Minimal v1 runtime:

```text
reverse proxy -> frontend
reverse proxy -> gateway -> auth_service -> postgres
                         -> expense_service -> postgres
                         -> loan_service -> postgres
                         -> analytics_service -> expense/loan services (+ optional redis)
```

Recommended v1 Compose profile:

```text
nginx
frontend
gateway
auth_service
expense_service
loan_service
analytics_service
postgres
redis optional
```

## 8. Services to Disable or Postpone

### Disable/Postpone for v1

| Area | Components | Reason |
|---|---|---|
| AI | `multi_agent_system`, `ollama`, MongoDB memory, Langfuse/LangSmith | High complexity, high resource use, unclear production safety |
| Kubernetes | `infra/k8s`, `infra/helm`, `scripts/task3`, k3d workflow | Too much operational weight for first VPS |
| Istio | `infra/istio`, rate limit EnvoyFilter, circuit breaker DestinationRules | Not needed for single VPS Docker deployment |
| ArgoCD | `infra/argocd`, CI sync workflow | Useful later, but not before stable container release |
| Heavy monitoring | Prometheus, Grafana, Loki, Promtail, Jaeger, OTEL collector | Postpone until baseline deploy is stable |
| Kafka/event backbone | Kafka, Zookeeper, `kafka-init` | Useful architecture, but expensive operationally; replace with direct writes or simple background jobs for v1 |
| MinIO | Object storage routes and MinIO service | Postpone unless receipt uploads are required at launch |
| Notification Service | Notification DB, consumers | Postpone unless v1 includes user-visible notifications |
| Terraform/Ansible cluster files | Cluster provisioning/Kafka deployment | Not needed for initial VPS |

### Keep as Documentation or Future Track

The platform work is valuable as a future roadmap. It should be kept but clearly separated from the production v1 path, for example:

```text
infra/
  docker/
  nginx/
  production-compose/
  labs/
    k8s/
    helm/
    argocd/
    istio/
    observability/
    terraform/
    ansible/
```

Do not do that restructuring until after the v1 runtime is defined and working.

## 9. Frontend Status and Rebuild Recommendation

### Current Frontend Status

Current stack:

| Item | Current State |
|---|---|
| Framework | React 18 + Vite |
| Language | JavaScript JSX |
| Routing | `react-router-dom` |
| Charts | `recharts` |
| Pages | Login, Register, Dashboard, Expenses, Loans, Analytics, AI Assistant |
| Styling | Multiple CSS files under `frontend/src/styles` |
| API layer | Plain JS modules under `frontend/src/api` |
| Docker runtime | Vite dev server on port `3000` |

Current frontend issues:

1. It runs as a development server in Docker.
2. It uses JavaScript rather than TypeScript, so API contracts are weak.
3. Styling is split across custom CSS files, likely harder to maintain as product UI grows.
4. It includes AI assistant UI even though AI should be postponed for v1.
5. It is a demo frontend rather than a product-grade financial application.

### Recommendation

Rebuild frontend with:

```text
Next.js + TypeScript + Tailwind CSS + shadcn/ui
```

Recommended v1 frontend features:

| Area | Required v1 Scope |
|---|---|
| Auth | Login/register/logout, token persistence, protected routes |
| Dashboard | Balance/summary cards, recent transactions, budget progress |
| Expenses | Add/edit/delete expenses and income, filters, categories |
| Budgets | Monthly budget setup and tracking |
| Loans | Add/edit/delete loans, status, paid amount |
| Analytics | Simple charts, monthly trend, category breakdown |
| Settings | Profile/security basics |

Frontend rebuild principles:

1. Remove AI Assistant from v1 navigation.
2. Use typed API clients and shared TypeScript DTOs.
3. Make the gateway the only browser API target.
4. Use server-side production build, not Vite dev server.
5. Design for mobile-first personal finance usage.
6. Keep UI dense, practical, and product-focused.

## 10. Production Blockers Before VPS Deployment

Critical blockers:

1. No production Compose file exists.
2. Current frontend Dockerfile runs a dev server.
3. Secrets use development defaults in `.env.example` and Kubernetes manifests.
4. Database migration strategy is not visible.
5. Too many services are required by the current Compose graph for a first VPS.
6. AI/Ollama will require significant CPU/RAM/disk and should not block core finance launch.
7. Kafka/Zookeeper add major operational complexity and no clear v1 necessity.
8. Internal admin ports are exposed to host in Compose.
9. No TLS/HTTPS production setup is defined.
10. No backup/restore procedure is defined for PostgreSQL.
11. No clear production logging policy exists after disabling heavy observability.
12. No healthcheck/dependency readiness strategy is defined in Compose for app services.
13. No rate limiting/auth hardening plan is visible for production gateway routes.
14. No CORS/domain policy audit is visible.
15. CI workflow assumes self-hosted runner, k3d registry, Kaniko, Helm tag mutation, and ArgoCD; it is not a normal VPS deploy pipeline.
16. Terraform state files are present in the repo and should be removed from version control history/process before real infra use.
17. Tests are mainly load scripts; unit/integration/e2e release tests are missing or not visible.
18. Notification/event consumer behavior depends on Kafka, which should not be required for v1.
19. Kubernetes config and Compose database topology disagree.
20. Public API contract/versioning is not formalized.

## 11. Step-by-Step Cleanup Roadmap

### Phase 1: Freeze Scope

1. Define AMMA Real v1 as: auth, expenses, categories, budgets, loans, basic analytics.
2. Mark AI, notifications, Kafka events, MinIO receipts, Kubernetes, Istio, ArgoCD, and heavy observability as v2/lab scope.
3. Decide whether loans are mandatory in v1. If not, postpone loan service too.
4. Document the v1 service list in `README.md` or a new production deployment doc.

### Phase 2: Create a Lean Runtime

1. Add a dedicated production-oriented Compose file later, for example `docker-compose.prod.yml`.
2. Use one PostgreSQL container/service for v1.
3. Keep only internal ports for backend services and databases.
4. Expose only reverse proxy ports `80` and `443`.
5. Remove AI/Kafka/observability dependencies from the v1 startup path.
6. Add healthchecks for gateway, services, and PostgreSQL.

### Phase 3: Harden Configuration

1. Split `.env.example` into local and production examples.
2. Remove development secrets from production documentation.
3. Require strong `JWT_SECRET_KEY`.
4. Add explicit production variables for allowed origins, public API URL, and frontend URL.
5. Define backup variables and storage paths for PostgreSQL.
6. Keep secrets out of committed Kubernetes manifests.

### Phase 4: Database Discipline

1. Add Alembic migrations per service or per unified database.
2. Define schema ownership clearly.
3. Create initial migration files from current models.
4. Add migration commands to deployment docs.
5. Add backup/restore scripts and test them locally.

### Phase 5: Frontend Rebuild

1. Create a new Next.js + TypeScript app.
2. Add Tailwind CSS and shadcn/ui.
3. Build typed API clients against gateway endpoints.
4. Implement auth and protected layout first.
5. Implement expenses, budgets, loans, and dashboard.
6. Add analytics charts after CRUD flows are stable.
7. Remove AI assistant from v1 navigation.
8. Build with production Docker image, not dev server.

### Phase 6: Backend Product Hardening

1. Audit JWT validation across services.
2. Add input validation tests for auth, expenses, budgets, loans.
3. Add integration tests through gateway endpoints.
4. Add consistent error responses and status codes.
5. Add pagination/filtering where list endpoints can grow.
6. Add ownership checks so users cannot access other users' financial records.
7. Add seed/demo data only as an explicit local command.

### Phase 7: Deployment Pipeline

1. Replace the k3d/Kaniko/ArgoCD workflow for v1 with a simple Docker image build and VPS deploy workflow.
2. Add image tagging policy.
3. Add `docker compose pull && docker compose up -d` deployment instructions or an automated SSH deploy job.
4. Add rollback instructions.
5. Add smoke tests after deployment.

### Phase 8: Minimal Observability

1. Start with structured container logs.
2. Add `/health` checks to all public/internal services.
3. Add basic uptime monitoring outside the VPS.
4. Add Prometheus/Grafana later only after v1 is stable.
5. Add tracing only when debugging real production bottlenecks.

### Phase 9: Future Platform Track

1. Move Kubernetes, Helm, ArgoCD, Istio, Kafka, and heavy observability into a clearly labeled lab/future folder later.
2. Keep diagrams and task reports as architecture references.
3. Reintroduce Kafka only when event replay/audit is a real product requirement.
4. Reintroduce AI only after the core finance product has real user workflows and data safety controls.
5. Reintroduce MinIO when receipt uploads or report export become production features.

## Recommended AMMA Real v1 Target

The practical production target should be:

```text
Browser
  -> HTTPS reverse proxy
    -> Next.js frontend
    -> Gateway API
      -> Auth Service
      -> Expense Service
      -> Loan Service
      -> Analytics Service
      -> PostgreSQL
      -> Redis optional
```

Everything else should be treated as future platform capability, not launch infrastructure.

## Final Recommendation

AMMA should stop trying to deploy the full academic platform as the first product. The codebase has enough pieces to become a real app, but the production path must be simplified aggressively.

The next best move is to define a lean `AMMA Real v1` runtime, rebuild the frontend with Next.js + TypeScript + Tailwind + shadcn/ui, consolidate production configuration, add migrations/tests/backups, and deploy only the finance core to a VPS. AI and platform engineering should return after the product is usable, secure, and maintainable.
