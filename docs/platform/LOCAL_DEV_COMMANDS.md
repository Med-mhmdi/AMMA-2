# Local Development Commands

This document collects the main local development commands, URLs, test credentials, and validation checks for the AMMA platform. It is intended as a quick reference for starting the system, testing the AI agent, and validating Kafka and Redis behavior in Docker Compose.

## 1. Project Startup

Start the full local platform with Docker Compose:

```bash
docker compose up --build -d
```

This builds and starts the backend services, databases, Kafka, Redis, observability stack, MinIO, Ollama, frontend container, and Nginx route.

## 2. Frontend Startup

For local frontend development with Vite, start the frontend separately:

```bash
cd frontend
npm run dev
```

## 3. Main Local URLs

| Component | URL | Notes |
| --- | --- | --- |
| Frontend | <http://localhost:3000> | React frontend served by the Docker container. |
| Gateway Swagger | <http://localhost:8000/docs> | FastAPI OpenAPI UI for the API gateway. |
| Nginx health route | <http://localhost/api/health> | Nginx route to the gateway health endpoint. |
| Grafana | <http://localhost:3001> | Observability dashboards. |
| Prometheus | <http://localhost:9090> | Metrics database and query UI. |
| MinIO Console | <http://localhost:9001> | Object storage console. |
| Jaeger | <http://localhost:16686> | Distributed tracing UI. |
| Loki readiness | <http://localhost:3100/ready> | Loki readiness endpoint. |
| Ollama | <http://localhost:11434> | Local LLM runtime endpoint. |

## 4. Test User Credentials

Use the following credentials for local login tests:

```json
{
  "email": "moh@gmail.com",
  "password": "1234567890"
}
```

## 5. Agent Endpoints

| Endpoint | URL | Purpose |
| --- | --- | --- |
| LangGraph Mermaid source | <http://localhost:8005/agent/graph/mermaid/raw> | Returns the raw Mermaid graph for the agent workflow. |

## 6. Agent Example Requests

Use these example payloads when testing the agent analysis endpoint.

```json
{
  "user_id": 1,
  "session_id": "confirm-test-1",
  "message": "I went to university by bus and came back today. It cost 46 each way. Add it to my expenses in the Transport category."
}
```

```json
{
  "user_id": 1,
  "session_id": "test-5",
  "message": "I bought a T-shirt for 550 rubles on 29/04/2026. Add it."
}
```

```json
{
  "user_id": 1,
  "session_id": "test-6",
  "message": "I received 1000 rubles for making a presentation for my friend. Add it."
}
```

## 7. Kafka Validation Commands

List Kafka topics:

```bash
docker exec -it amma_kafka kafka-topics --bootstrap-server kafka:9092 --list
```

Consume expense creation events:

```bash
docker exec -it amma_kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic expense.created --from-beginning
```

Follow analytics service logs:

```bash
docker compose logs -f analytics_service
```

## 8. Redis Validation Commands

Check Redis connectivity:

```bash
docker exec -it amma_redis redis-cli ping
```

Expected response:

```text
PONG
```

List Redis keys:

```bash
docker exec -it amma_redis redis-cli KEYS "*"
```

## 9. Expected Results and Notes

- Docker Compose should start all services in detached mode.
- The frontend should be available at `http://localhost:3000`.
- The gateway Swagger UI should be available at `http://localhost:8000/docs`.
- Kafka topic listing should show the AMMA business event topics, including `expense.created`.
- Consuming `expense.created` should display new expense events after expense creation.
- Analytics logs should show cache invalidation activity when relevant Kafka events are consumed.
- Redis should return `PONG` for the ping command.
- Redis is used as the caching layer for analytics. It stores computed dashboard, category, and daily summaries to reduce repeated calculations.
