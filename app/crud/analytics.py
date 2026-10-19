from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.tables import Tables

tables = Tables()


def _today_for_timezone(timezone_name: str | None) -> date:
    try:
        zone = ZoneInfo(timezone_name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")
    return datetime.now(zone).date()


async def get_user_weekly_summary(
    user_id: UUID,
    db: AsyncSession,
    timezone_name: str = "UTC",
) -> dict[str, Any]:
    today = _today_for_timezone(timezone_name)
    start_date = today - timedelta(days=6)
    checkins = tables.daily_checkins
    result = await db.execute(
        select(
            checkins.c.date,
            checkins.c.mood,
            checkins.c.focus_percent,
        )
        .where(
            checkins.c.user_id == user_id,
            checkins.c.date >= start_date,
            checkins.c.date <= today,
        )
        .order_by(checkins.c.date.asc())
    )
    rows = result.mappings().all()
    if not rows:
        return {
            "start_date": start_date.isoformat(),
            "end_date": today.isoformat(),
            "entry_count": 0,
            "days": [],
        }

    focus_values = [
        float(row["focus_percent"])
        for row in rows
        if row["focus_percent"] is not None
    ]
    moods = Counter(row["mood"] for row in rows if row["mood"])
    days = [
        {
            "date": row["date"].isoformat(),
            "mood": row["mood"],
            "focus_percent": row["focus_percent"],
        }
        for row in rows
    ]
    summary = {
        "start_date": start_date.isoformat(),
        "end_date": today.isoformat(),
        "entry_count": len(rows),
        "days": days,
    }
    if focus_values:
        summary["average_focus"] = round(sum(focus_values) / len(focus_values), 2)
    if moods:
        summary["most_common_mood"] = moods.most_common(1)[0][0]
    return summary


async def get_user_monthly_summary(
    user_id: UUID,
    db: AsyncSession,
    timezone_name: str = "UTC",
) -> dict[str, Any]:
    today = _today_for_timezone(timezone_name)
    first_day = today.replace(day=1)
    checkins = tables.daily_checkins
    result = await db.execute(
        select(
            checkins.c.date,
            checkins.c.mood,
            checkins.c.focus_percent,
        )
        .where(
            checkins.c.user_id == user_id,
            checkins.c.date >= first_day,
            checkins.c.date <= today,
        )
        .order_by(checkins.c.date.asc())
    )
    rows = result.mappings().all()
    if not rows:
        return {
            "start_date": first_day.isoformat(),
            "end_date": today.isoformat(),
            "entry_count": 0,
            "mood_distribution": {},
            "focus_trend": [],
        }

    focus_values = [
        float(row["focus_percent"])
        for row in rows
        if row["focus_percent"] is not None
    ]
    mood_distribution = Counter(row["mood"] for row in rows if row["mood"])
    weeks: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row["focus_percent"] is None:
            continue
        iso = row["date"].isocalendar()
        weeks[f"{iso.year}-W{iso.week:02d}"].append(float(row["focus_percent"]))

    result_data: dict[str, Any] = {
        "start_date": first_day.isoformat(),
        "end_date": today.isoformat(),
        "entry_count": len(rows),
        "mood_distribution": dict(mood_distribution),
        "focus_trend": [
            {
                "week": label,
                "average_focus": round(sum(values) / len(values), 2),
            }
            for label, values in sorted(weeks.items())
        ],
    }
    if focus_values:
        result_data["average_focus"] = round(sum(focus_values) / len(focus_values), 2)
    return result_data


async def get_user_tag_summary(user_id: UUID, db: AsyncSession) -> dict[str, Any]:
    counts: Counter[str] = Counter()

    for table in (tables.journal_entries, tables.daily_checkins):
        result = await db.execute(
            select(table.c.tags).where(table.c.user_id == user_id)
        )
        for row in result.mappings().all():
            for tag in row["tags"] or []:
                if isinstance(tag, str) and tag.strip():
                    counts[tag.strip().lstrip("#").lower()] += 1

    return {
        "top_tags": [
            {"tag": tag, "count": count}
            for tag, count in counts.most_common(20)
        ]
    }
