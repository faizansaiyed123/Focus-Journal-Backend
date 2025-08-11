from fastapi import status, HTTPException
from typing import List, Dict
from uuid import UUID
from sqlalchemy import text, select, and_
from app.schemas.checkin import *
from app.db.tables import Tables
from app.crud.insights import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
from openai import AsyncOpenAI, OpenAIError
from app.core.config import settings

OPENAI_API_KEY = settings.OPENAI_API_KEY
tables = Tables()

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_journal_insights(user_id: UUID, db: AsyncSession) -> dict:
    journal_entries = tables.journal_entries

    query = (
        select(journal_entries)
        .where(journal_entries.c.user_id == user_id)
        .order_by(journal_entries.c.created_at.desc())
    )
    result = await db.execute(query)
    entries = [row.content for row in result.fetchall()]

    if not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No journal entries found."
        )

    combined_text = "\n".join(entries)[-4000:]

    prompt = f"""
    You are a journal analysis assistant. Analyze the following journal content and provide:
    1. A short summary of the user's overall mood.
    2. A focus score from 0 to 100 based on how focused and productive the text sounds.
    3. A list of the top 5 keywords that appear frequently.

    Journal Content:
    {combined_text}
    """

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        parsed = response.choices[0].message.content.strip()
        lines = parsed.splitlines()

        # Extract mood summary
        mood_summary = (
            next((line for line in lines if "mood" in line.lower()), "")
            .split(":", 1)[-1]
            .strip()
        )

        # Extract and safely parse focus score
        try:
            focus_line = next((line for line in lines if "focus" in line.lower()), "Focus: 0")
            raw_focus = focus_line.split(":")[-1].strip().split()[0]
            focus_score = int(float(raw_focus))  # 💡 Safe parsing
        except (ValueError, IndexError):
            focus_score = 0  # Default to 0 if parsing fails

        # Extract keywords
        keywords_line = next((line for line in lines if "keyword" in line.lower()), "")
        top_keywords = [
            kw.strip().strip(".,") for kw in keywords_line.split(":")[-1].split(",") if kw.strip()
        ]

        return {
            "mood_summary": mood_summary,
            "focus_score": focus_score,
            "top_keywords": top_keywords,
        }

    except OpenAIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI API error: {str(e)}",
        )


async def get_top_journal_tags(user_id: int, db: AsyncSession) -> List[Dict[str, int]]:
    query = text(
        """
        SELECT tag, COUNT(*) as count
        FROM (
            SELECT UNNEST(tags) AS tag
            FROM journal_entries
            WHERE user_id = :user_id
        ) AS all_tags
        GROUP BY tag
        ORDER BY count DESC
        LIMIT 20;
    """
    )

    try:
        result = await db.execute(query, {"user_id": user_id})
        rows = result.fetchall()
        tags = [{"tag": row.tag, "count": row.count} for row in rows]
        return tags

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch journal tags: {str(e)}",
        )


async def search_journal_entries_by_keyword(
    user_id: UUID, keyword: str, db: AsyncSession
) -> List[dict]:
    daily_checkins = tables.daily_checkins

    try:
        query = (
            select(
                daily_checkins.c.id,
                daily_checkins.c.date,
                daily_checkins.c.note,
                daily_checkins.c.tags,
                daily_checkins.c.mood,
                daily_checkins.c.focus_percent,
            )
            .where(
                and_(
                    daily_checkins.c.user_id == user_id,
                    or_(
                        daily_checkins.c.note.ilike(f"%{keyword}%"),
                        text(f"'{keyword}' = ANY(tags)"),
                    ),
                )
            )
            .order_by(daily_checkins.c.date.desc())
        )

        result = await db.execute(query)
        rows = result.fetchall()

        return [
            {
                "id": row.id,
                "date": row.date.isoformat(),
                "note": row.note,
                "tags": row.tags,
                "mood": row.mood,
                "focus_percent": row.focus_percent,
            }
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search journal entries: {str(e)}",
        )


async def get_journal_calendar_data(user_id: UUID, db: AsyncSession) -> dict:
    checkins = tables.daily_checkins

    query = (
        select(checkins)
        .where(checkins.c.user_id == user_id)
        .order_by(checkins.c.date.desc())
    )

    try:
        result = await db.execute(query)
        rows = result.fetchall()

        calendar_data = {}
        for row in rows:
            date_str = row.date.isoformat()
            calendar_data.setdefault(date_str, []).append(
                {
                    "id": str(row.id),
                    "note": row.note,
                    "tags": row.tags,
                    "mood": row.mood,
                    "focus_percent": row.focus_percent,
                }
            )

        return calendar_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch journal calendar data: {str(e)}",
        )
