import json
import os
import threading
import time
from collections.abc import Callable
from typing import Any

from kafka import KafkaConsumer


def start_kafka_consumer_thread(
    *,
    topics: list[str],
    group_id: str,
    handler: Callable[[dict[str, Any]], None],
    service_name: str,
) -> threading.Thread:
    """Start a daemon consumer thread with reconnect loop."""

    def _run() -> None:
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

        while True:
            try:
                consumer = KafkaConsumer(
                    *topics,
                    bootstrap_servers=bootstrap_servers,
                    value_deserializer=lambda message: json.loads(message.decode("utf-8")),
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                    group_id=group_id,
                )
                print(f"[{service_name}] Kafka consumer started. topics={topics} group={group_id}")

                for message in consumer:
                    try:
                        handler(message.value)
                    except Exception as exc:
                        print(f"[{service_name}] Failed to process Kafka event: {exc}")

            except Exception as exc:
                print(f"[{service_name}] Kafka connection failed: {exc}. Retrying in 5 seconds...")
                time.sleep(5)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
