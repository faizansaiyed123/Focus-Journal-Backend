from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def user_local_today(user: dict):
    timezone_name = user.get("timezone") or "UTC"
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        zone = timezone.utc
    return datetime.now(zone).date()
