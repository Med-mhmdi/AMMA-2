# AMMA Kafka Topics

AMMA uses Kafka as the event backbone for Event-Driven Architecture (EDA). Kafka was selected because financial events should be durable, replayable, and consumable by multiple services independently.

## Main topics

| Topic | Producer | Consumers | Purpose |
|---|---|---|---|
| `user.created` | Auth Service | Notification, Analytics | User onboarding event |
| `expense.created` | Expense Service | Notification, Analytics | New financial transaction |
| `expense.updated` | Expense Service | Analytics | Recalculate analytics/cache |
| `expense.deleted` | Expense Service | Analytics | Recalculate analytics/cache |
| `budget.updated` | Expense Service | Analytics, Notification | Budget warning and dashboard update |
| `loan.created` | Loan Service | Notification, Analytics | New loan/reminder data |
| `loan.updated` | Loan Service | Analytics, Notification | Loan status/amount changed |
| `loan.deleted` | Loan Service | Analytics | Loan removed |
| `notification.created` | Notification Service | Audit/future delivery worker | Track notification lifecycle |
| `notification.sent` | Notification Service | Audit/future analytics | Notification delivery completed |
| `ai.insight.generated` | Multi-Agent Service | Notification, Analytics | AI-generated financial insight |
| `analytics.snapshot.created` | Analytics Service | Agent, cold storage pipeline | Precomputed analytics snapshot |

## Dead-letter topics

Each topic has a `.dlq` variant for failed events. Example: `expense.created.dlq`.

## Standard event envelope

```json
{
  "event_id": "uuid",
  "event_type": "expense.created",
  "event_version": 1,
  "source_service": "expense_service",
  "occurred_at": "2026-05-22T10:00:00Z",
  "correlation_id": "uuid",
  "user_id": 1,
  "payload": {}
}
```

## Broker comparison for defense

| Broker | Strength | Weakness | AMMA decision |
|---|---|---|---|
| RabbitMQ | Simple task queues, routing, request/reply | Weaker for long replayable event history | Good for direct jobs, not best for analytics replay |
| NATS | Very fast lightweight pub/sub | Needs JetStream for durability; less demonstrative for event history | Good for low-latency messages, not ideal as main financial event log |
| Kafka | Durable log, replay, consumer groups, stream processing | Heavier infra and operational complexity | Best fit for AMMA analytics, notifications, audit, and RecSys pipelines |
