# app/services/checkin_summary.py

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.db.tables import Tables

tables = Tables()


async def get_user_weekly_summary(user_id: str, db: AsyncSession):

    try:
        checkins = tables.daily_checkins
    except AttributeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Check-in table not defined in Tables schema.",
        )

    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=6)

    query = (
        select(
            func.date(checkins.c.date).label("date"),
            func.avg(checkins.c.focus_percent).label("focus_percent"),
            func.mode().within_group(checkins.c.mood).label("mood"),  # PostgreSQL only
        )
        .where(
            checkins.c.user_id == user_id,
            checkins.c.date >= week_ago,
            checkins.c.date <= today,
        )
        .group_by(func.date(checkins.c.date))
        .order_by(func.date(checkins.c.date))
    )

    result = await db.execute(query)
    rows = result.fetchall()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No check-in data found for the past 7 days.",
        )

    if any(r.focus_percent is None or r.mood is None for r in rows):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Some records are missing required fields (mood or focus).",
        )

    average_focus = round(sum([r.focus_percent for r in rows]) / len(rows))
    moods = [r.mood for r in rows]
    most_common_mood = max(set(moods), key=moods.count)

    return {
        "days": [
            {
                "date": str(r.date),
                "mood": r.mood,
                "focus_percent": round(r.focus_percent),
            }
            for r in rows
        ],
        "average_focus": average_focus,
        "most_common_mood": most_common_mood,
    }


async def get_user_monthly_summary(user_id: str, db: AsyncSession):

    try:
        checkins = tables.daily_checkins
    except AttributeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Check-in table is not properly configured.",
        )

    today = datetime.utcnow().date()
    first_day = today.replace(day=1)

    # 1. Average focus
    focus_query = select(func.avg(checkins.c.focus_percent)).where(
        checkins.c.user_id == user_id, checkins.c.date >= first_day
    )
    focus_result = await db.execute(focus_query)
    average_focus = focus_result.scalar()
    if average_focus is None:
        average_focus = 0

    # 2. Mood distribution
    mood_query = (
        select(checkins.c.mood, func.count().label("count"))
        .where(checkins.c.user_id == user_id, checkins.c.date >= first_day)
        .group_by(checkins.c.mood)
    )
    mood_result = await db.execute(mood_query)
    mood_distribution = {row.mood: row.count for row in mood_result.fetchall()}

    # 3. Focus trend by week
    week_trunc = func.date_trunc("week", checkins.c.date).label("week")

    week_query = (
        select(week_trunc, func.avg(checkins.c.focus_percent).label("average_focus"))
        .where(checkins.c.user_id == user_id, checkins.c.date >= first_day)
        .group_by(week_trunc)
        .order_by(week_trunc)
    )
    week_result = await db.execute(week_query)
    focus_trend = [
        {"week": row.week.strftime("%Y-W%U"), "average_focus": round(row.average_focus)}
        for row in week_result.fetchall()
        if row.average_focus is not None
    ]

    return {
        "average_focus": round(average_focus),
        "mood_distribution": mood_distribution,
        "focus_trend": focus_trend,
    }


async def get_user_tag_summary(user_id: str, db: AsyncSession):
    tables = Tables()

    try:
        checkins = tables.daily_checkins
    except AttributeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Check-in table is not properly configured.",
        )

    query = select(checkins.c.tags).where(checkins.c.user_id == user_id)
    result = await db.execute(query)

    all_tags = []
    for row in result.fetchall():
        if row.tags:
            all_tags.extend(row.tags if isinstance(row.tags, list) else [])

    tag_count = {}
    for tag in all_tags:
        tag_count[tag] = tag_count.get(tag, 0) + 1

    top_tags = sorted(
        [{"tag": k, "count": v} for k, v in tag_count.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    return {"top_tags": top_tags}
