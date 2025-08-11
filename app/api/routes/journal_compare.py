from fastapi import APIRouter, Depends, Request, HTTPException
from datetime import date
from typing import List
from pydantic import BaseModel
from sqlalchemy import select
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.db.tables import Tables

router = APIRouter()

MOOD_SCORES = {"bad": 1, "okay": 2, "good": 3, "great": 4}


class CompareDates(BaseModel):
    start_range_1: date
    end_range_1: date
    start_range_2: date
    end_range_2: date




def parse_tags(tag_data) -> List[str]:
    if isinstance(tag_data, list):
        # Already a list, just strip whitespace and filter out empties
        return [tag.strip() for tag in tag_data if isinstance(tag, str) and tag.strip()]
    elif isinstance(tag_data, str):
        # Comma-separated string
        return [tag.strip() for tag in tag_data.split(",") if tag.strip()]
    return []



# ✅ Pass db session into the function
async def analyze_range(
    table, user_id: int, start_date: date, end_date: date, db: AsyncSession
):
    try:
        query = (
            select(table.c.focus_percent, table.c.mood, table.c.tags)
            .where(table.c.user_id == user_id)
            .where(table.c.date >= start_date)
            .where(table.c.date <= end_date)
        )

        result = await db.execute(query)
        rows = result.fetchall()

        if not rows:
            return {
                "average_focus": 0,
                "average_mood": 0,
                "entry_count": 0,
                "common_tags": [],
            }

        focus_scores = []
        mood_scores = []
        all_tags_flat = []

        for row in rows:
            if row.focus_percent is not None:
                focus_scores.append(row.focus_percent)

            mood = row.mood
            if mood in MOOD_SCORES:
                mood_scores.append(MOOD_SCORES[mood])

            tags = row.tags
            if tags:
                all_tags_flat.extend(parse_tags(tags))

        most_common = [tag for tag, _ in Counter(all_tags_flat).most_common(3)]

        return {
            "average_focus": (
                round(sum(focus_scores) / len(focus_scores)) if focus_scores else 0
            ),
            "average_mood": (
                round(sum(mood_scores) / len(mood_scores), 1) if mood_scores else 0
            ),
            "entry_count": len(rows),
            "common_tags": most_common,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze range: {str(e)}"
        )


# 🚀 Journal comparison endpoint
@router.post("/journal/compare")
async def compare_journal_periods(
    body: CompareDates,
    request: Request,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tables = Tables()
    checkins = tables.daily_checkins

    range1 = await analyze_range(
        checkins, user["id"], body.start_range_1, body.end_range_1, db
    )
    range2 = await analyze_range(
        checkins, user["id"], body.start_range_2, body.end_range_2, db
    )

    return {
        "message": "Comparison retrieved successfully.",
        "data": {"range_1": range1, "range_2": range2},
    }
