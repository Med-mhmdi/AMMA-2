#!/usr/bin/env bash
set -e

BOOTSTRAP_SERVER="${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"
PARTITIONS="${KAFKA_PARTITIONS:-3}"
REPLICATION_FACTOR="${KAFKA_REPLICATION_FACTOR:-1}"

TOPICS=(
  "user.created"
  "expense.created"
  "expense.updated"
  "expense.deleted"
  "budget.updated"
  "loan.created"
  "loan.updated"
  "loan.deleted"
  "notification.created"
  "notification.sent"
  "ai.insight.generated"
  "analytics.snapshot.created"
)

echo "Waiting for Kafka at ${BOOTSTRAP_SERVER}..."
until kafka-topics --bootstrap-server "${BOOTSTRAP_SERVER}" --list >/dev/null 2>&1; do
  sleep 3
done

for topic in "${TOPICS[@]}"; do
  echo "Creating topic: ${topic}"
  kafka-topics \
    --bootstrap-server "${BOOTSTRAP_SERVER}" \
    --create \
    --if-not-exists \
    --topic "${topic}" \
    --partitions "${PARTITIONS}" \
    --replication-factor "${REPLICATION_FACTOR}"

  echo "Creating DLQ topic: ${topic}.dlq"
  kafka-topics \
    --bootstrap-server "${BOOTSTRAP_SERVER}" \
    --create \
    --if-not-exists \
    --topic "${topic}.dlq" \
    --partitions 1 \
    --replication-factor "${REPLICATION_FACTOR}"
done

echo "Kafka topics are ready."
kafka-topics --bootstrap-server "${BOOTSTRAP_SERVER}" --list
