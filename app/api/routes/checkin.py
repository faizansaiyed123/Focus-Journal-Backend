from fastapi import APIRouter, Depends, status, Query
from typing import List
from uuid import UUID
from sqlalchemy import text
from schemas.checkin import *
from crud.checkin import *
from core.dependencies import get_current_user
from db.session import get_db

router = APIRouter(prefix="/checkin", tags=["Check-ins"])


@router.get("/", response_model=List[CheckinOut])
async def fetch_all_checkins(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_checkins(user["id"], db)


# Create a new check-in
@router.post("/", response_model=CheckinOut, status_code=status.HTTP_201_CREATED)
async def create_new_checkin(
    payload: CheckinCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_checkin(user_id=user["id"], payload=payload, db=db)


@router.get("/checkins", summary="List all check-ins (optionally between dates)")
async def list_checkins(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = user["id"]
    checkins_table = Tables().daily_checkins

    query = select(checkins_table).where(checkins_table.c.user_id == user_id)

    if start_date:
        query = query.where(checkins_table.c.date >= start_date)
    if end_date:
        query = query.where(checkins_table.c.date <= end_date)

    query = query.order_by(checkins_table.c.date.desc())
    result = await db.execute(query)
    data = result.mappings().all()

    return {"success": True, "data": data, "message": "Check-ins fetched successfully"}


@router.get("/checkin/today", summary="Check if user has checked in today")
async def check_if_checked_in_today(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    checkin_table = Tables().daily_checkins

    query = select(checkin_table).where(
        checkin_table.c.user_id == current_user["id"],
        checkin_table.c.date == today,
    )
    result = await db.execute(query)
    checkin = result.first()

    return {
        "success": True,
        "message": "Checked in today" if checkin else "Not checked in today",
        "data": {"checked_in": bool(checkin)},
    }


@router.get("/checkin/stats")
async def get_checkin_stats(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    query = text(
        """
    SELECT 
        COUNT(*) AS total_checkins,
        COALESCE(AVG(focus_percent), 0) AS average_focus,
        COALESCE(AVG(sleep_duration), 0) AS average_sleep
    FROM daily_checkins
    WHERE user_id = :user_id
"""
    )

    result = await db.execute(query, {"user_id": current_user["id"]})
    row = result.mappings().first()

    return {"success": True, "message": "Check-in stats retrieved", "data": row or {}}


@router.get("/checkin/history", summary="Get recent check-in history")
async def get_checkin_history(
    range: int = Query(
        7, ge=1, le=30, description="Number of recent check-ins to retrieve"
    ),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = text(
        """
         SELECT 
            date,
            mood,
            focus_percent,
            tags,
            note
        FROM daily_checkins
        WHERE user_id = :user_id
        ORDER BY date DESC
        LIMIT :limit
    """
    )
    result = await db.execute(query, {"user_id": current_user["id"], "limit": range})

    rows = result.mappings().all()

    return {
        "success": True,
        "message": f"Last {range} check-ins retrieved",
        "data": [dict(r) for r in rows],
    }



@router.get("/streak", response_model=StreakOut)
async def fetch_user_streak(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_user_streak(user_id=user["id"], db=db)


# Get check-in by ID
@router.get("/by-id/{checkin_id}", response_model=CheckinOut)
async def fetch_checkin_by_id(
    checkin_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_checkin_by_id(user["id"], checkin_id, db)


# Update check-in
@router.put("/{checkin_id}", response_model=CheckinOut)
async def update_checkin(
    checkin_id: UUID,
    payload: CheckinUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_checkin_by_id(
        user_id=user["id"], checkin_id=checkin_id, payload=payload, db=db
    )


# Delete check-in
@router.delete("/{checkin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkin(
    checkin_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_checkin_by_id(user_id=user["id"], checkin_id=checkin_id, db=db)
    return None
