from shared.amma_events.event_models import build_event
from shared.amma_events.producers import KafkaEventProducer
from shared.amma_events.topics import Topics


class LoanEventPublisher:
    """Publishes loan-related events to Kafka using the shared AMMA event envelope."""

    def __init__(self):
        self.producer = KafkaEventProducer(client_id="loan-service")

    def publish_loan_created(self, payload: dict):
        event = build_event(
            event_type=Topics.LOAN_CREATED,
            source_service="loan_service",
            user_id=payload.get("user_id"),
            payload=payload,
        )
        self.producer.publish(Topics.LOAN_CREATED, event, key=payload.get("user_id"))

    def publish_loan_updated(self, payload: dict):
        event = build_event(
            event_type=Topics.LOAN_UPDATED,
            source_service="loan_service",
            user_id=payload.get("user_id"),
            payload=payload,
        )
        self.producer.publish(Topics.LOAN_UPDATED, event, key=payload.get("user_id"))

    def publish_loan_deleted(self, payload: dict):
        event = build_event(
            event_type=Topics.LOAN_DELETED,
            source_service="loan_service",
            user_id=payload.get("user_id"),
            payload=payload,
        )
        self.producer.publish(Topics.LOAN_DELETED, event, key=payload.get("user_id"))
