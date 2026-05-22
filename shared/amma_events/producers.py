import json
import os
import time
from typing import Any

from kafka import KafkaProducer


class KafkaEventProducer:
    def __init__(self, bootstrap_servers: str | None = None, client_id: str | None = None):
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self.client_id = client_id or os.getenv("KAFKA_CLIENT_ID", "amma-service")
        self._producer: KafkaProducer | None = None

    def _get_producer(self) -> KafkaProducer:
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
                key_serializer=lambda value: str(value).encode("utf-8") if value is not None else None,
                acks="all",
                retries=5,
                retry_backoff_ms=500,
            )
        return self._producer

    def publish(self, topic: str, event: dict[str, Any], key: str | int | None = None) -> None:
        producer = self._get_producer()
        producer.send(topic, key=key, value=event)
        producer.flush(timeout=10)

    def close(self) -> None:
        if self._producer is not None:
            self._producer.flush(timeout=10)
            self._producer.close(timeout=10)
            self._producer = None
