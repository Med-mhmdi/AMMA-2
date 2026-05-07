import json
import threading
import time

from kafka import KafkaConsumer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.notification import Notification


KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
LOAN_TOPIC = "loan.created"
GROUP_ID = "notification-loan-group"


def consume_loan_events():
    while True:
        try:
            consumer = KafkaConsumer(
                LOAN_TOPIC,
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
                        title="Loan created",
                        message=f"Loan recorded for {event['person_name']} amount {event['amount']}",
                        type="loan_reminder",
                        status="pending",
                        related_entity_id=event["loan_id"],
                    )
                    db.add(notification)
                    db.commit()
                finally:
                    db.close()

        except Exception as exc:
            print(f"[Loan Consumer] Kafka connection failed: {exc}")
            time.sleep(5)


def start_loan_consumer():
    thread = threading.Thread(target=consume_loan_events, daemon=True)
    thread.start()