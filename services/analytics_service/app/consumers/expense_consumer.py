from app.services.cache_service import CacheService
from shared.amma_events.consumers import start_kafka_consumer_thread
from shared.amma_events.topics import Topics


CACHE_EVENTS = [
    Topics.EXPENSE_CREATED,
    Topics.EXPENSE_UPDATED,
    Topics.EXPENSE_DELETED,
    Topics.BUDGET_UPDATED,
    Topics.LOAN_CREATED,
    Topics.LOAN_UPDATED,
    Topics.LOAN_DELETED,
]


def _extract_user_id(event: dict) -> int | None:
    if event.get("user_id") is not None:
        return event.get("user_id")
    payload = event.get("payload") or event
    return payload.get("user_id")


def handle_financial_event(event: dict) -> None:
    """
    Invalidate analytics cache when the source financial data changes.
    This keeps Analytics mostly REST-compatible while still proving EDA behavior.
    """
    user_id = _extract_user_id(event)
    if user_id is None:
        print(f"[analytics_service] Skipped event without user_id: {event}")
        return

    deleted = CacheService().invalidate_user_cache(int(user_id))
    print(f"[analytics_service] invalidated {deleted} cache keys for user_id={user_id}")


def start_analytics_consumer():
    return start_kafka_consumer_thread(
        topics=CACHE_EVENTS,
        group_id="analytics-cache-invalidation-group",
        handler=handle_financial_event,
        service_name="analytics_service",
    )
