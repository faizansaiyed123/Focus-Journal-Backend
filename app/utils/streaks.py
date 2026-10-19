from datetime import date, timedelta
from typing import Iterable


def calculate_streak_stats(
    checkin_dates: Iterable[date],
    *,
    today: date,
) -> tuple[int, int, date | None]:
    dates = sorted(set(checkin_dates))
    if not dates:
        return 0, 0, None

    longest = 1
    run = 1
    for previous, current in zip(dates, dates[1:]):
        if current == previous + timedelta(days=1):
            run += 1
        else:
            longest = max(longest, run)
            run = 1
    longest = max(longest, run)

    latest = dates[-1]
    if latest not in (today, today - timedelta(days=1)):
        return 0, longest, latest

    current_streak = 1
    cursor = latest
    date_set = set(dates)
    while cursor - timedelta(days=1) in date_set:
        cursor -= timedelta(days=1)
        current_streak += 1
    return current_streak, longest, latest
