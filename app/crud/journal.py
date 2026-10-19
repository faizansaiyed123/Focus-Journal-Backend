from collections import Counter
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.tables import Tables
from schemas.journal import JournalEntryCreate, UpdateJournalEntry
from utils.sentiment import get_sentiment_score

tables = Tables()


def _normalize_entry(row) -> dict:
    entry = dict(row)
    entry["tags"] = entry.get("tags") or []
    entry["is_favorite"] = bool(entry.get("is_favorite", False))
    return entry


async def get_journal_entries_by_user(user_id: UUID, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(tables.journal_entries)
        .where(tables.journal_entries.c.user_id == user_id)
        .order_by(tables.journal_entries.c.created_at.desc())
    )
    return [_normalize_entry(row) for row in result.mappings().all()]


async def create_journal_entry(entry: JournalEntryCreate, user_id: UUID, db: AsyncSession) -> dict:
    result = await db.execute(
        insert(tables.journal_entries)
        .values(
            user_id=user_id,
            title=entry.title,
            content=entry.content,
            mood=entry.mood,
            is_favorite=entry.is_favorite,
            focus_percent=entry.focus_percent,
            tags=entry.tags,
        )
        .returning(tables.journal_entries)
    )
    await db.commit()
    return _normalize_entry(result.mappings().one())


async def get_journal_entry_by_id_service(entry_id: UUID, user_id: UUID, db: AsyncSession) -> dict:
    result = await db.execute(
        select(tables.journal_entries).where(
            tables.journal_entries.c.id == entry_id,
            tables.journal_entries.c.user_id == user_id,
        )
    )
    entry = result.mappings().first()
    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return _normalize_entry(entry)


async def update_journal_entry_service(
    entry_id: UUID,
    user_id: UUID,
    data: UpdateJournalEntry,
    db: AsyncSession,
) -> dict:
    existing = await db.execute(
        select(tables.journal_entries.c.id).where(
            tables.journal_entries.c.id == entry_id,
            tables.journal_entries.c.user_id == user_id,
        )
    )
    if existing.first() is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    values = data.model_dump(exclude_unset=True)
    if not values:
        return await get_journal_entry_by_id_service(entry_id, user_id, db)
    if values.get("title", "valid") is None:
        raise HTTPException(status_code=422, detail="Title cannot be null")
    if values.get("is_favorite", "valid") is None:
        raise HTTPException(status_code=422, detail="Favorite status cannot be null")
    if "tags" in values and values["tags"] is None:
        values["tags"] = []

    result = await db.execute(
        update(tables.journal_entries)
        .where(
            tables.journal_entries.c.id == entry_id,
            tables.journal_entries.c.user_id == user_id,
        )
        .values(**values)
        .returning(tables.journal_entries)
    )
    await db.commit()
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return _normalize_entry(row)


async def delete_journal_entry_service(entry_id: UUID, user_id: UUID, db: AsyncSession) -> None:
    result = await db.execute(
        delete(tables.journal_entries).where(
            tables.journal_entries.c.id == entry_id,
            tables.journal_entries.c.user_id == user_id,
        )
    )
    if result.rowcount == 0:
        await db.rollback()
        raise HTTPException(status_code=404, detail="Journal entry not found")
    await db.commit()


async def get_user_journal_stats(user_id: UUID, db: AsyncSession) -> dict[str, Any]:
    stats_result = await db.execute(
        select(
            func.count(tables.journal_entries.c.id).label("total_entries"),
            func.avg(tables.journal_entries.c.focus_percent).label("average_focus"),
        ).where(tables.journal_entries.c.user_id == user_id)
    )
    stats = stats_result.mappings().one()

    moods_result = await db.execute(
        select(tables.journal_entries.c.mood, func.count().label("count"))
        .where(
            tables.journal_entries.c.user_id == user_id,
            tables.journal_entries.c.mood.is_not(None),
        )
        .group_by(tables.journal_entries.c.mood)
        .order_by(func.count().desc())
        .limit(3)
    )
    tags_result = await db.execute(
        select(tables.journal_entries.c.tags).where(
            tables.journal_entries.c.user_id == user_id
        )
    )
    tag_counter: Counter[str] = Counter()
    for row in tags_result.mappings().all():
        for tag in row["tags"] or []:
            normalized = tag.strip().lower()
            if normalized:
                tag_counter[normalized] += 1

    return {
        "total_entries": stats["total_entries"] or 0,
        "average_focus": round(float(stats["average_focus"] or 0), 2),
        "most_common_moods": [row["mood"] for row in moods_result.mappings().all()],
        "most_used_tags": [tag for tag, _ in tag_counter.most_common(3)],
    }


async def get_sentiment_analysis_data(user_id: UUID, db: AsyncSession) -> dict:
    result = await db.execute(
        select(tables.daily_checkins.c.date, tables.daily_checkins.c.note)
        .where(tables.daily_checkins.c.user_id == user_id)
        .order_by(tables.daily_checkins.c.date.asc())
    )
    entries = result.mappings().all()
    grouped: dict[str, list[float]] = {}
    for row in entries:
        date_key = row["date"].isoformat()
        grouped.setdefault(date_key, []).append(get_sentiment_score(row["note"] or ""))

    trend = [
        {"date": day, "sentiment_score": round(sum(scores) / len(scores), 2)}
        for day, scores in sorted(grouped.items())
        if scores
    ]
    return {"message": "Sentiment analysis retrieved successfully.", "data": trend}


async def get_weekly_summary_data(
    user_id: UUID,
    db: AsyncSession,
    timezone_name: str = "UTC",
) -> dict:
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")
    today = datetime.now(zone).date()
    start_date = today - timedelta(days=6)
    checkins = tables.daily_checkins

    result = await db.execute(
        select(
            func.avg(checkins.c.focus_percent).label("avg_focus"),
            func.count().label("entry_count"),
            func.array_agg(checkins.c.tags).label("tags_array"),
        ).where(
            checkins.c.user_id == user_id,
            checkins.c.date >= start_date,
            checkins.c.date <= today,
        )
    )
    summary = result.mappings().one()
    if not summary["entry_count"]:
        return {
            "message": "No check-ins found for this week.",
            "data": {
                "start_date": str(start_date),
                "end_date": str(today),
                "average_focus": 0,
                "common_tags": [],
                "entry_count": 0,
            },
        }

    all_tags: list[str] = []
    for taglist in summary["tags_array"] or []:
        if taglist:
            all_tags.extend(tag.strip().lower() for tag in taglist if tag and tag.strip())
    common_tags = [tag for tag, _ in Counter(all_tags).most_common(5)]

    return {
        "message": "Weekly summary retrieved successfully.",
        "data": {
            "start_date": str(start_date),
            "end_date": str(today),
            "average_focus": round(float(summary["avg_focus"] or 0), 2),
            "common_tags": common_tags,
            "entry_count": summary["entry_count"],
        },
    }
