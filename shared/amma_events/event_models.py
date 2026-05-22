from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_event(
    *,
    event_type: str,
    source_service: str,
    user_id: int | None,
    payload: dict[str, Any],
    correlation_id: str | None = None,
    event_version: int = 1,
) -> dict[str, Any]:
    """
    Standard event envelope used across AMMA.

    This makes Kafka communication defendable because every event has:
    - event identity
    - type/version
    - source service
    - user ownership
    - correlation id for tracing a user request across services
    - payload with business data
    """
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "event_version": event_version,
        "source_service": source_service,
        "occurred_at": utc_now_iso(),
        "correlation_id": correlation_id or str(uuid4()),
        "user_id": user_id,
        "payload": payload,
    }
