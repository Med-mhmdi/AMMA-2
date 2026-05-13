from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Europe/Moscow"


def get_today_iso(timezone: str | None = None) -> str:
    """
    Return today's date using the app/user timezone.

    Default is Europe/Moscow for local development.
    Later, this should come from the user profile, frontend request,
    or session settings.
    """
    tz = timezone or DEFAULT_TIMEZONE
    return datetime.now(ZoneInfo(tz)).date().isoformat()