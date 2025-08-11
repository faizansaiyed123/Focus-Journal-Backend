from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from sqlalchemy import select, func
from fastapi import status
from fastapi import HTTPException
from sqlalchemy import insert, update, delete, text
from app.schemas.journal import *
from app.db.tables import Tables
from typing import Dict
from collections import Counter
from datetime import date, timedelta
from app.utils.sentiment import get_sentiment_score

# Initialize table access
tables = Tables()


async def get_journal_entries_by_user(user_id: str, db: AsyncSession):
    query = select(tables.journal_entries).where(
        tables.journal_entries.c.user_id == user_id
    )
    result = await db.execute(query)
    return result.mappings().all()


async def create_journal_entry(
    entry: JournalEntryCreate, user_id: str, db: AsyncSession
):
    insert_stmt = (
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

    result = await db.execute(insert_stmt)
    await db.commit()
    return result.mappings().first()


async def get_journal_entry_by_id_service(
    entry_id: uuid, user_id: uuid, db: AsyncSession
) -> dict:  # Or use your JournalEntryResponse Pydantic model here
    query = select(tables.journal_entries).where(
        tables.journal_entries.c.id == entry_id,
        tables.journal_entries.c.user_id == user_id,
    )
    result = await db.execute(query)
    entry = result.mappings().one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return dict(entry)  # if you want to convert RowMapping to a regular dict


async def update_journal_entry_service(
    entry_id: UUID, user_id: UUID, data: UpdateJournalEntry, db: AsyncSession
):
    # Ensure entry exists and belongs to user
    query = select(tables.journal_entries).where(
        tables.journal_entries.c.id == entry_id,
        tables.journal_entries.c.user_id == user_id,
    )
    result = await db.execute(query)
    existing_entry = result.mappings().one_or_none()

    if not existing_entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    update_stmt = (
        update(tables.journal_entries)
        .where(
            tables.journal_entries.c.id == entry_id,
            tables.journal_entries.c.user_id == user_id,
        )
        .values(**data.dict(exclude_unset=True))
        .returning(tables.journal_entries)
    )
    updated_result = await db.execute(update_stmt)
    await db.commit()
    return updated_result.mappings().first()


async def delete_journal_entry_service(entry_id: UUID, user_id: UUID, db: AsyncSession):
    # Optional: Check if the entry exists before deleting
    query = select(tables.journal_entries).where(
        tables.journal_entries.c.id == entry_id,
        tables.journal_entries.c.user_id == user_id,
    )
    result = await db.execute(query)
    entry = result.mappings().one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    delete_stmt = delete(tables.journal_entries).where(
        tables.journal_entries.c.id == entry_id,
        tables.journal_entries.c.user_id == user_id,
    )
    await db.execute(delete_stmt)
    await db.commit()


async def get_user_journal_stats(user_id: str, db: AsyncSession) -> Dict:
    # Total entries and average focus
    stats_query = text(
        """
        SELECT COUNT(*) AS total_entries, AVG(focus_percent) AS average_focus
        FROM journal_entries
        WHERE user_id = :user_id
    """
    )
    stats_result = await db.execute(stats_query, {"user_id": user_id})
    stats = stats_result.mappings().first()

    if not stats:
        return {}

    # Mood count
    mood_query = text(
        """
        SELECT mood, COUNT(*) AS count
        FROM journal_entries
        WHERE user_id = :user_id AND mood IS NOT NULL
        GROUP BY mood
        ORDER BY count DESC
        LIMIT 3
    """
    )
    mood_result = await db.execute(mood_query, {"user_id": user_id})
    common_moods = [row[0] for row in mood_result.fetchall()]

    # Tag processing
    tags_query = text(
        """
    SELECT UNNEST(tags) AS tag
    FROM journal_entries
    WHERE user_id = :user_id AND tags IS NOT NULL
"""
    )

    tag_result = await db.execute(tags_query, {"user_id": user_id})
    tag_counter = {}
    for row in tag_result.fetchall():
        tag = row[0].strip().lower()
        if tag:
            tag_counter[tag] = tag_counter.get(tag, 0) + 1

    top_tags = sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)[:3]
    top_tag_names = [tag for tag, _ in top_tags]

    return {
        "total_entries": stats["total_entries"],
        "average_focus": round(stats["average_focus"] or 0, 2),
        "most_common_moods": common_moods,
        "most_used_tags": top_tag_names,
    }


async def get_sentiment_analysis_data(user_id: str, db: AsyncSession) -> dict:
    try:
        checkins = tables.daily_checkins

        query = (
            select(checkins)
            .where(checkins.c.user_id == user_id)
            .order_by(checkins.c.created_at.asc())
        )
        result = await db.execute(query)
        entries = result.mappings().all()

        trend = {}
        for row in entries:
            date_str = row["created_at"].strftime("%Y-%m-%d")
            content = row["note"] or ""  # ✅ use note, not content
            score = get_sentiment_score(content)
            trend.setdefault(date_str, []).append(score)

        data = [
            {"date": date, "sentiment_score": round(sum(scores) / len(scores), 2)}
            for date, scores in trend.items()
        ]

        return {
            "message": "Sentiment analysis retrieved successfully.",
            "data": sorted(data, key=lambda x: x["date"]),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze sentiment: {str(e)}",
        )


async def get_weekly_summary_data(user_id: UUID, db: AsyncSession) -> dict:
    try:
        today = date.today()
        start_date = today - timedelta(days=6)
        checkins = Tables().daily_checkins

        query = select(
            func.avg(checkins.c.focus_percent).label("avg_focus"),
            func.count().label("entry_count"),
            func.array_agg(checkins.c.tags).label("tags_array"),
        ).where(
            checkins.c.user_id == user_id,
            checkins.c.date >= start_date,
            checkins.c.date <= today,
        )

        result = await db.execute(query)
        summary = result.mappings().first()

        if not summary or summary["entry_count"] == 0:
            return {"message": "No entries found for this week.", "data": {}}

        # Flatten and normalize tags
        all_tags = []
        for taglist in summary["tags_array"]:
            if taglist:
                all_tags.extend([tag.strip().lower() for tag in taglist if tag])

        tag_counts = Counter(all_tags)
        common_tags = [tag for tag, _ in tag_counts.most_common(5)]

        return {
            "message": "Weekly summary retrieved successfully.",
            "data": {
                "start_date": str(start_date),
                "end_date": str(today),
                "average_focus": round(summary["avg_focus"] or 0, 2),
                "common_tags": common_tags,
                "entry_count": summary["entry_count"],
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weekly summary: {str(e)}",
        )
