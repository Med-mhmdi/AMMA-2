from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.notification import Notification
from shared.amma_events.consumers import start_kafka_consumer_thread
from shared.amma_events.topics import Topics


def _payload(event: dict) -> dict:
    return event.get("payload") or event


def handle_expense_event(event: dict) -> None:
    payload = _payload(event)
    db: Session = SessionLocal()
    try:
        notification = Notification(
            user_id=payload["user_id"],
            title="Expense created",
            message=f"New {payload.get('category', 'unknown')} expense: {payload.get('amount')}",
            type="system_message",
            status="pending",
            related_entity_id=payload.get("expense_id"),
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()


def start_expense_consumer():
    return start_kafka_consumer_thread(
        topics=[Topics.EXPENSE_CREATED],
        group_id="notification-expense-group",
        handler=handle_expense_event,
        service_name="notification_service.expense_consumer",
    )
