from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, model_validator
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user
from db.session import get_db
from db.tables import Tables

router = APIRouter(tags=["Journal comparison"])
tables = Tables()


class CompareDates(BaseModel):
    start_range_1: date
    end_range_1: date
    start_range_2: date
    end_range_2: date

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.start_range_1 > self.end_range_1:
            raise ValueError("Range 1 start date must not be after its end date")
        if self.start_range_2 > self.end_range_2:
            raise ValueError("Range 2 start date must not be after its end date")
        return self


def _range_bounds(
    start_date: date,
    end_date: date,
    timezone_name: str,
) -> tuple[datetime, datetime, ZoneInfo]:
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")

    start_at = datetime.combine(start_date, time.min, tzinfo=zone).astimezone(timezone.utc)
    end_at = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
        tzinfo=zone,
    ).astimezone(timezone.utc)
    return start_at, end_at, zone


async def analyze_range(
    user_id: UUID,
    start_date: date,
    end_date: date,
    timezone_name: str,
    db: AsyncSession,
) -> dict[str, Any]:
    start_at, end_at, zone = _range_bounds(start_date, end_date, timezone_name)
    entries = tables.journal_entries
    try:
        result = await db.execute(
            select(
                entries.c.id,
                entries.c.title,
                entries.c.created_at,
                entries.c.mood,
                entries.c.focus_percent,
                entries.c.tags,
            )
            .where(
                entries.c.user_id == user_id,
                entries.c.created_at >= start_at,
                entries.c.created_at < end_at,
            )
            .order_by(entries.c.created_at.asc())
        )
        rows = result.mappings().all()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Journal period comparison could not be completed",
        ) from None

    if not rows:
        return {"days": [], "entry_count": 0}

    focus_scores = [
        float(row["focus_percent"])
        for row in rows
        if row["focus_percent"] is not None
    ]
    mood_counts = Counter(row["mood"] for row in rows if row["mood"])
    tag_counts: Counter[str] = Counter()
    days = []
    for row in rows:
        for tag in row["tags"] or []:
            if isinstance(tag, str) and tag.strip():
                tag_counts[tag.strip().lstrip("#").lower()] += 1
        created_at = row["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        days.append(
            {
                "date": created_at.astimezone(zone).date().isoformat(),
                "title": row["title"],
                "mood": row["mood"],
                "focus_percent": row["focus_percent"],
            }
        )

    data: dict[str, Any] = {
        "days": days,
        "entry_count": len(rows),
        "common_tags": [tag for tag, _ in tag_counts.most_common(3)],
    }
    if focus_scores:
        data["average_focus"] = round(sum(focus_scores) / len(focus_scores), 2)
    if mood_counts:
        data["most_common_mood"] = mood_counts.most_common(1)[0][0]
    return data


@router.post("/journal/compare")
async def compare_journal_periods(
    body: CompareDates,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    timezone_name = user.get("timezone") or "UTC"
    range1 = await analyze_range(
        user["id"],
        body.start_range_1,
        body.end_range_1,
        timezone_name,
        db,
    )
    range2 = await analyze_range(
        user["id"],
        body.start_range_2,
        body.end_range_2,
        timezone_name,
        db,
    )
    return {
        "message": "Journal comparison retrieved successfully",
        "data": {"range_1": range1, "range_2": range2},
    }
