# AMMA

AMMA stands for **AI Money Management Assistant**.

It is a distributed financial management platform designed as a **microservices-based system** with an **AI multi-agent subsystem**. The system allows users to manage expenses, income, loans, analytics, notifications, and AI-generated financial insights.

## Project Goals

AMMA is being developed for two purposes at the same time:

1. as an academic software engineering project covering system design, multi-agent systems, and distributed architecture
2. as a production-oriented foundation for a future real product

## Main Architecture

The project is organized as a **monorepo**, while the runtime architecture follows a **microservices approach**.

### Core services

- API Gateway
- Auth Service
- Expense Service
- Loan Service
- Analytics Service
- AI Agent Service
- Notification Service

### Infrastructure and supporting components

- PostgreSQL for transactional relational data
- MongoDB for agent memory and flexible AI-related storage
- Redis for caching
- Kafka for event-driven communication
- Nginx for routing and reverse proxy
- MinIO for cold storage
- Prometheus, Grafana, Loki, and Jaeger for observability
- Docker Compose for local development
- Kubernetes-ready manifests for future orchestration

## Repository Structure

```text
docs/        -> reports, architectural decisions, evaluation notes
infra/       -> Docker, Nginx, Kafka, Redis, MongoDB, observability, k8s
shared/      -> shared Python packages and internal clients
services/    -> backend microservices
frontend/    -> React + Vite frontend
tests/       -> integration and end-to-end tests