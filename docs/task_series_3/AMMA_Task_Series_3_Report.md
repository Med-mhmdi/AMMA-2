# AMMA Task Series 3 Report

## 1. Project Overview

AMMA, AI Money Management Assistant, is a microservices-based financial assistant. The system allows users to manage income, expenses, categories, budgets, loans, notifications, analytics dashboards, and AI-powered financial advice. The project is implemented using FastAPI microservices, a React frontend, PostgreSQL databases, MongoDB for agent memory, Redis caching, Kafka for event-driven communication, MinIO for object storage, and a local LLM runtime through Ollama.

## 2. Communication Between Microservices: Kafka and EDA

AMMA uses both synchronous and asynchronous communication. Synchronous REST calls are used when the frontend needs an immediate response through the API Gateway. Asynchronous Kafka communication is used for financial domain events such as expense creation, loan creation, budget updates, notification creation, and future AI insight generation.

### Kafka Event Flow

When a user creates an expense, the Expense Service writes the transaction to PostgreSQL and publishes an `expense.created` event to Kafka. The Notification Service consumes this event and creates a user notification. The Analytics Service also consumes the event and invalidates the Redis analytics cache for the affected user. This means the dashboard is recalculated after financial data changes.

### Kafka vs RabbitMQ vs NATS

| Broker | Strengths | Weaknesses | Fit for AMMA |
|---|---|---|---|
| RabbitMQ | Simple task queues, routing, request/reply | Less suitable for replayable event history | Good for direct jobs, but weaker for analytics replay |
| NATS | Very fast lightweight pub/sub | Requires JetStream for durable history | Good for low latency, but less useful as the main financial event log |
| Kafka | Durable log, replay, consumer groups, scalable event streaming | Heavier and more complex | Best fit because AMMA needs event replay, analytics recalculation, auditability, and future RecSys pipelines |

Kafka was chosen because AMMA benefits from durable, replayable financial events. This is useful for analytics, notification generation, audit trails, and future recommendation pipelines.

## 3. Data Layer: RDBMS + NoSQL + Cold Storage

AMMA uses polyglot persistence.

| Data | Storage |
|---|---|
| Users | PostgreSQL Auth DB |
| Expenses, categories, budgets | PostgreSQL Expense DB |
| Loans | PostgreSQL Loan DB |
| Notifications | PostgreSQL Notification DB |
| AI agent working memory | MongoDB |
| Fast analytics cache | Redis |
| Event stream | Kafka |
| Receipts, exported reports, archived snapshots | MinIO |

PostgreSQL is used for transactional data because it provides structured schemas and consistency. MongoDB is used for flexible AI memory because conversation context and agent state can change shape over time. MinIO is used as S3-compatible object storage for cold data such as receipts, reports, and old analytics snapshots.

## 4. Redis-like Caching

Redis is used by the Analytics Service to cache expensive dashboard and chart responses. The cache keys follow the pattern:

```text
analytics:{user_id}:categories:{year}:{month}:{period}:{transaction_type}
analytics:{user_id}:daily:{year}:{month}
```

When financial events are published through Kafka, the Analytics Service consumes them and invalidates the related user's Redis keys. This improves performance while keeping the dashboard consistent after expenses, loans, or budgets change.

## 5. Routing Layer: Router + Balancer + Rate Limiter

The routing layer is implemented with Nginx and the FastAPI API Gateway.

- Nginx acts as the external entry point.
- `/api/` requests are routed to the API Gateway.
- `/` requests are routed to the React frontend.
- Rate limiting is applied at the Nginx level with `limit_req_zone`.
- The API Gateway routes requests to Auth, Expense, Loan, Analytics, Notification, and Agent services.

This gives AMMA a clear edge layer and protects internal microservices from request bursts.

## 6. C4 Diagrams

The updated C4 set contains seven diagrams:

1. System Context Diagram
2. Container Diagram
3. API Gateway Component Diagram
4. Expense Service Component Diagram
5. Multi-Agent Service Component Diagram
6. Event-Driven Sequence Diagram for Expense Creation
7. Deployment Diagram

These diagrams are stored under `docs/c4/` as Mermaid files.

## 7. Infrastructure Part

The local infrastructure is managed with Docker Compose. The stack includes:

- Nginx
- React frontend
- API Gateway
- Auth, Expense, Loan, Analytics, Multi-Agent, and Notification services
- PostgreSQL databases
- MongoDB
- Redis
- Kafka and Zookeeper
- MinIO
- Ollama
- Prometheus
- Grafana
- Loki
- Jaeger

The project also contains Kubernetes manifests as the migration target. The production-grade direction is to deploy these services inside a Kubernetes namespace, add Cilium for networking policies and observability, use an Ingress Controller, add Helm charts, and later automate deployment with ArgoCD.

## 8. Observability

AMMA includes a basic observability stack:

- Prometheus for metrics collection
- Grafana for dashboards
- Loki for logs
- Jaeger for traces
- Langfuse or LangSmith for LLM/agent observability

The current implementation provides the observability containers and configuration. The next production improvement is to add Prometheus `/metrics` middleware to every FastAPI service and OpenTelemetry traces to Jaeger.

## 9. Load Testing

A Locust test file is included under `tests/load/locustfile.py`. It simulates user behavior such as login, listing expenses, creating expenses, viewing analytics, listing loans, and reading notifications. This supports validation of the Gateway, microservices, Kafka event generation, Redis cache behavior, and rate limiter behavior.

## 10. Limitations and Future Improvements

Current limitations:

- Some Kubernetes files are still initial manifests, not a full production deployment.
- Prometheus service metrics need proper `/metrics` endpoints.
- Kafka currently supports the main events, but retry topics and DLQ processing can be improved.
- MinIO is available, but upload/report features should be connected to application logic.
- Service mesh, Cilium, ArgoCD, and Helm are documented as the target infrastructure but not fully implemented.

Future improvements:

- Add OpenTelemetry instrumentation to all services.
- Add Helm charts for Gateway, Expense, Loan, and Notification services.
- Add ArgoCD App-of-Apps structure.
- Add Kafka DLQ consumers.
- Add MinIO receipt upload and monthly report export.
- Add a full Recommendation Service pipeline.
