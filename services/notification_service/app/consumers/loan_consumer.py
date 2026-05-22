from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.notification import Notification
from shared.amma_events.consumers import start_kafka_consumer_thread
from shared.amma_events.topics import Topics


def _payload(event: dict) -> dict:
    return event.get("payload") or event


def handle_loan_event(event: dict) -> None:
    payload = _payload(event)
    db: Session = SessionLocal()
    try:
        notification = Notification(
            user_id=payload["user_id"],
            title="Loan created",
            message=f"Loan recorded for {payload.get('person_name', 'unknown')} amount {payload.get('amount')}",
            type="loan_reminder",
            status="pending",
            related_entity_id=payload.get("loan_id"),
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()


def start_loan_consumer():
    return start_kafka_consumer_thread(
        topics=[Topics.LOAN_CREATED],
        group_id="notification-loan-group",
        handler=handle_loan_event,
        service_name="notification_service.loan_consumer",
    )
