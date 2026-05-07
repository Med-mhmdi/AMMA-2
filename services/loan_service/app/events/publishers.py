import json
from kafka import KafkaProducer


KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
LOAN_TOPIC = "loan.created"


class LoanEventPublisher:
    """Publishes loan-related events to Kafka."""

    def __init__(self):
        self.producer = None

    def _get_producer(self):
        if self.producer is None:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        return self.producer

    def publish_loan_created(self, payload: dict):
        producer = self._get_producer()
        producer.send(LOAN_TOPIC, payload)
        producer.flush()