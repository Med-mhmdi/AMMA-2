import json
import threading
import time

from kafka import KafkaConsumer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.notification import Notification


KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
EXPENSE_TOPIC = "expense.created"
GROUP_ID = "notification-expense-group"


def consume_expense_events():
    while True:
        try:
            consumer = KafkaConsumer(
                EXPENSE_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id=GROUP_ID,
            )

            for message in consumer:
                event = message.value

                db: Session = SessionLocal()
                try:
                    notification = Notification(
                        user_id=event["user_id"],
                        title="Expense created",
                        message=f"New {event['category']} expense: {event['amount']}",
                        type="system_message",
                        status="pending",
                        related_entity_id=event["expense_id"],
                    )
                    db.add(notification)
                    db.commit()
                finally:
                    db.close()

        except Exception as exc:
            print(f"[Expense Consumer] Kafka connection failed: {exc}")
            time.sleep(5)


def start_expense_consumer():
    thread = threading.Thread(target=consume_expense_events, daemon=True)
    thread.start()