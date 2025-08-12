from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.checkin import CheckinCreate, CheckinUpdate
from db.tables import Tables
from sqlalchemy import select, insert, update, delete, and_
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status


def get_current_timestamp():
    return datetime.now(timezone.utc)


tables = Tables()


# Get all check-ins
async def get_all_checkins(user_id: UUID, db: AsyncSession):
    checkin_table = tables.daily_checkins
    query = (
        select(checkin_table)
        .where(checkin_table.c.user_id == user_id)
        .order_by(checkin_table.c.created_at.desc())
    )
    result = await db.execute(query)
    return result.mappings().all()


# # Create a check-in
# async def create_checkin(user_id: UUID, payload: CheckinCreate, db: AsyncSession):
#     # Check if one already exists
#     check_query = select(tables.daily_checkins).where(
#         and_(
#             tables.daily_checkins.c.user_id == user_id,
#             tables.daily_checkins.c.date == payload.checkin_date
#         )
#     )
#     existing = await db.execute(check_query)
#     if existing.first():
#         raise HTTPException(status_code=409, detail="Check-in for this date already exists.")

#     now = get_current_timestamp()
#     insert_stmt = (
#         insert(tables.daily_checkins)
#         .values(
#             user_id=user_id,
#             date=payload.checkin_date,
#             mood=payload.mood,
#             focus_percent=payload.focus_percent,
#             tags=payload.tags,
#             note=payload.note,
#             created_at=now,
#             updated_at=now,
#         )
#         .returning(tables.daily_checkins)
#     )
#     result = await db.execute(insert_stmt)
#     await db.commit()
#     return result.mappings().first()


async def create_checkin(user_id: UUID, payload: CheckinCreate, db: AsyncSession):
    # Check for existing check-in
    check_query = select(tables.daily_checkins).where(
        and_(
            tables.daily_checkins.c.user_id == user_id,
            tables.daily_checkins.c.date == payload.checkin_date,
        )
    )
    existing = await db.execute(check_query)
    if existing.first():
        raise HTTPException(
            status_code=409, detail="Check-in for this date already exists."
        )

    now = get_current_timestamp()

    # Insert the new check-in
    insert_stmt = (
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
    result = await db.execute(insert_stmt)
    checkin_row = result.mappings().first()

    # -------------------------------
    # 🔁 Streak update logic
    # -------------------------------
    streak_query = select(tables.user_streaks).where(
        tables.user_streaks.c.user_id == user_id
    )

    streak_result = await db.execute(streak_query)
    streak = streak_result.mappings().first()

    today = payload.checkin_date
    yesterday = today - timedelta(days=1)

    if not streak:
        # First-time streak
        insert_streak = insert(tables.user_streaks).values(
            user_id=user_id,
            current_streak=1,
            longest_streak=1,
            last_checkin_date=today,
            created_at=now,
            updated_at=now,
        )
        await db.execute(insert_streak)
    else:
        # Calculate new streak
        current_streak = streak["current_streak"]
        longest_streak = streak["longest_streak"]
        last_date = streak["last_checkin_date"]

        if last_date == yesterday:
            current_streak += 1
        elif last_date == today:
            # Already counted today's streak
            pass
        else:
            current_streak = 1  # streak broken

        longest_streak = max(longest_streak, current_streak)

        update_stmt = (
            update(tables.user_streaks)
            .where(tables.user_streaks.c.user_id == user_id)
            .values(
                current_streak=current_streak,
                longest_streak=longest_streak,
                last_checkin_date=today,
                updated_at=now,
            )
        )
        await db.execute(update_stmt)

    await db.commit()
    return checkin_row


# Get check-in by ID
async def get_checkin_by_id(user_id: UUID, checkin_id: UUID, db: AsyncSession):
    query = select(tables.daily_checkins).where(
        tables.daily_checkins.c.id == checkin_id,
        tables.daily_checkins.c.user_id == user_id,
    )
    result = await db.execute(query)
    row = result.mappings().first()
    if not row:
        raise HTTPException("Check-in not found")
    return row


# Update check-in
async def update_checkin_by_id(
    user_id: UUID, checkin_id: UUID, payload: CheckinUpdate, db: AsyncSession
):
    # Check existence
    exists = await db.execute(
        select(tables.daily_checkins).where(
            tables.daily_checkins.c.id == checkin_id,
            tables.daily_checkins.c.user_id == user_id,
        )
    )
    if not exists.first():
        raise HTTPException("Check-in not found")

    update_stmt = (
        update(tables.daily_checkins)
        .where(tables.daily_checkins.c.id == checkin_id)
        .values(
            mood=payload.mood,
            note=payload.note,
            updated_at=get_current_timestamp(),
        )
        .returning(tables.daily_checkins)
    )
    result = await db.execute(update_stmt)
    await db.commit()
    return result.mappings().first()


# Delete check-in
async def delete_checkin_by_id(user_id: UUID, checkin_id: UUID, db: AsyncSession):
    exists = await db.execute(
        select(tables.daily_checkins).where(
            tables.daily_checkins.c.id == checkin_id,
            tables.daily_checkins.c.user_id == user_id,
        )
    )
    if not exists.first():
        raise HTTPException("Check-in not found")

    await db.execute(
        delete(tables.daily_checkins).where(
            tables.daily_checkins.c.id == checkin_id,
            tables.daily_checkins.c.user_id == user_id,
        )
    )
    await db.commit()



async def get_user_streak(user_id: UUID, db: AsyncSession) -> dict:
    checkins = tables.daily_checkins

    query = (
        select(checkins.c.date)
        .where(checkins.c.user_id == user_id)
        .order_by(checkins.c.date.asc())
    )

    try:
        result = await db.execute(query)
        dates = [row.date for row in result.fetchall()]

        if not dates:
            return {
                "user_id": user_id,
                "current_streak": 0,
                "longest_streak": 0,
                "last_checkin_date": None,
            }

        longest_streak = 1
        streak = 1

        for i in range(1, len(dates)):
            if dates[i] == dates[i - 1] + timedelta(days=1):
                streak += 1
            else:
                if streak > longest_streak:
                    longest_streak = streak
                streak = 1
        if streak > longest_streak:
            longest_streak = streak

        # Calculate current streak from the latest date backward
        last_checkin_date = dates[-1]
        current_streak = 0
        for i in range(len(dates) - 1, -1, -1):
            expected_date = last_checkin_date - timedelta(days=current_streak)
            if dates[i] == expected_date:
                current_streak += 1
            else:
                break

        return {
            "user_id": user_id,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_checkin_date": last_checkin_date.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating streaks: {str(e)}",
        )
