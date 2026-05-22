from shared.amma_events.event_models import build_event
from shared.amma_events.producers import KafkaEventProducer
from shared.amma_events.topics import Topics


class ExpenseEventPublisher:
    """Publishes expense-related events to Kafka using the shared AMMA event envelope."""

    def __init__(self):
        self.producer = KafkaEventProducer(client_id="expense-service")

    def publish_expense_created(self, payload: dict):
        event = build_event(
            event_type=Topics.EXPENSE_CREATED,
            source_service="expense_service",
            user_id=payload.get("user_id"),
            payload=payload,
        )
        self.producer.publish(Topics.EXPENSE_CREATED, event, key=payload.get("user_id"))

    def publish_expense_updated(self, payload: dict):
        event = build_event(
            event_type=Topics.EXPENSE_UPDATED,
            source_service="expense_service",
            user_id=payload.get("user_id"),
            payload=payload,
        )
        self.producer.publish(Topics.EXPENSE_UPDATED, event, key=payload.get("user_id"))

    def publish_expense_deleted(self, payload: dict):
        event = build_event(
            event_type=Topics.EXPENSE_DELETED,
            source_service="expense_service",
            user_id=payload.get("user_id"),
            payload=payload,
        )
        self.producer.publish(Topics.EXPENSE_DELETED, event, key=payload.get("user_id"))

    def publish_budget_updated(self, payload: dict):
        event = build_event(
            event_type=Topics.BUDGET_UPDATED,
            source_service="expense_service",
            user_id=payload.get("user_id"),
            payload=payload,
        )
        self.producer.publish(Topics.BUDGET_UPDATED, event, key=payload.get("user_id"))
