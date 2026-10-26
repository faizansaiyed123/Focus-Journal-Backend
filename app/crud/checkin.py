from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.tables import Tables
from schemas.checkin import CheckinCreate, CheckinUpdate
from utils.streaks import calculate_streak_stats

tables = Tables()


def _normalize_checkin(row) -> dict:
    checkin = dict(row)
    checkin["tags"] = checkin.get("tags") or []
    return checkin


async def get_all_checkins(user_id: UUID, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(tables.daily_checkins)
        .where(tables.daily_checkins.c.user_id == user_id)
        .order_by(tables.daily_checkins.c.date.desc())
    )
    return [_normalize_checkin(row) for row in result.mappings().all()]


async def create_checkin(user_id: UUID, payload: CheckinCreate, db: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    try:
        result = await db.execute(
            insert(tables.daily_checkins)
            .values(
                user_id=user_id,
                date=payload.checkin_date,
                mood=payload.mood,
                focus_percent=payload.focus_percent,
                tags=payload.tags,
                note=payload.note,
                created_at=now,
                updated_at=now,
            )
            .returning(tables.daily_checkins)
        )
        await db.commit()
        return _normalize_checkin(result.mappings().one())
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A check-in already exists for this date",
        ) from None


async def get_checkin_by_id(
    user_id: UUID,
    checkin_id: UUID,
    db: AsyncSession,
) -> dict:
    result = await db.execute(
        select(tables.daily_checkins).where(
            tables.daily_checkins.c.id == checkin_id,
            tables.daily_checkins.c.user_id == user_id,
        )
    )
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Check-in not found")
    return _normalize_checkin(row)


async def update_checkin_by_id(
    user_id: UUID,
    checkin_id: UUID,
    payload: CheckinUpdate,
    db: AsyncSession,
) -> dict:
    values = payload.model_dump(exclude_unset=True)
    if not values:
        return await get_checkin_by_id(user_id, checkin_id, db)
    if "mood" in values and values["mood"] is None:
        raise HTTPException(status_code=422, detail="Mood cannot be null")
    if "tags" in values and values["tags"] is None:
        values["tags"] = []
    values["updated_at"] = datetime.now(timezone.utc)

    try:
        result = await db.execute(
            update(tables.daily_checkins)
            .where(
                tables.daily_checkins.c.id == checkin_id,
                tables.daily_checkins.c.user_id == user_id,
            )
            .values(**values)
            .returning(tables.daily_checkins)
        )
        row = result.mappings().first()
        if row is None:
            await db.rollback()
            raise HTTPException(status_code=404, detail="Check-in not found")
        await db.commit()
        return _normalize_checkin(row)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=422,
            detail="Check-in fields do not satisfy the data constraints",
        ) from None


async def delete_checkin_by_id(user_id: UUID, checkin_id: UUID, db: AsyncSession) -> None:
    result = await db.execute(
        delete(tables.daily_checkins).where(
            tables.daily_checkins.c.id == checkin_id,
            tables.daily_checkins.c.user_id == user_id,
        )
    )
    if result.rowcount == 0:
        await db.rollback()
        raise HTTPException(status_code=404, detail="Check-in not found")
    await db.commit()


async def get_user_streak(user_id: UUID, db: AsyncSession, today) -> dict:
    result = await db.execute(
        select(tables.daily_checkins.c.date)
        .where(tables.daily_checkins.c.user_id == user_id)
        .order_by(tables.daily_checkins.c.date.asc())
    )
    dates = [row["date"] for row in result.mappings().all()]
    current, longest, last_date = calculate_streak_stats(dates, today=today)
    return {
        "user_id": user_id,
        "current_streak": current,
        "longest_streak": longest,
        "last_checkin_date": last_date,
    }
