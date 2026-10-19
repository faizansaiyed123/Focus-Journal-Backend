from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user
from db.session import get_db
from db.tables import Tables
from schemas.checkin import CheckinCreate, CheckinOut, CheckinUpdate, StreakOut
from crud.checkin import (
    create_checkin,
    delete_checkin_by_id,
    get_all_checkins,
    get_checkin_by_id,
    get_user_streak,
    update_checkin_by_id,
)
from utils.dates import user_local_today

router = APIRouter(prefix="/checkin", tags=["Check-ins"])
tables = Tables()


@router.get("/", response_model=list[CheckinOut])
async def fetch_all_checkins(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_checkins(user["id"], db)


@router.post("/", response_model=CheckinOut, status_code=status.HTTP_201_CREATED)
async def create_new_checkin(
    payload: CheckinCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.checkin_date > user_local_today(user):
        raise HTTPException(status_code=422, detail="A check-in cannot be dated in the future")
    return await create_checkin(user["id"], payload, db)


@router.get("/checkins", summary="List check-ins, optionally between dates")
async def list_checkins(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")

    checkins = tables.daily_checkins
    query = select(checkins).where(checkins.c.user_id == user["id"])
    if start_date:
        query = query.where(checkins.c.date >= start_date)
    if end_date:
        query = query.where(checkins.c.date <= end_date)
    query = query.order_by(checkins.c.date.desc())
    result = await db.execute(query)
    return {
        "success": True,
        "data": [dict(row) for row in result.mappings().all()],
        "message": "Check-ins fetched successfully",
    }


@router.get("/today", summary="Check whether the user has checked in today")
@router.get("/checkin/today", include_in_schema=False)
async def check_if_checked_in_today(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(tables.daily_checkins.c.id).where(
            tables.daily_checkins.c.user_id == user["id"],
            tables.daily_checkins.c.date == user_local_today(user),
        )
    )
    checked_in = result.first() is not None
    return {
        "success": True,
        "checked": checked_in,
        "message": "Checked in today" if checked_in else "Not checked in today",
        "data": {"checked_in": checked_in},
    }


@router.get("/stats", summary="Get check-in statistics")
@router.get("/checkin/stats", include_in_schema=False)
async def get_checkin_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    checkins = tables.daily_checkins
    result = await db.execute(
        select(
            func.count(checkins.c.id).label("total_checkins"),
            func.avg(checkins.c.focus_percent).label("average_focus"),
            func.avg(checkins.c.sleep_duration).label("average_sleep"),
        ).where(checkins.c.user_id == user["id"])
    )
    row = result.mappings().one()
    data = {
        "total_checkins": int(row["total_checkins"] or 0),
        "average_focus": round(float(row["average_focus"] or 0), 2),
        "average_sleep": round(float(row["average_sleep"] or 0), 2),
    }
    return {"success": True, "message": "Check-in stats retrieved", "data": data}


@router.get("/history", summary="Get recent check-in history")
@router.get("/checkin/history", include_in_schema=False)
async def get_checkin_history(
    range: int = Query(default=7, ge=1, le=90),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    checkins = tables.daily_checkins
    result = await db.execute(
        select(
            checkins.c.date,
            checkins.c.mood,
            checkins.c.focus_percent,
            checkins.c.tags,
            checkins.c.note,
        )
        .where(checkins.c.user_id == user["id"])
        .order_by(checkins.c.date.desc())
        .limit(range)
    )
    return {
        "success": True,
        "message": f"Last {range} check-ins retrieved",
        "data": [dict(row) for row in result.mappings().all()],
    }


@router.get("/streak", response_model=StreakOut)
async def fetch_user_streak(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_user_streak(user_id=user["id"], db=db, today=user_local_today(user))


@router.get("/by-id/{checkin_id}", response_model=CheckinOut)
async def fetch_checkin_by_id(
    checkin_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_checkin_by_id(user["id"], checkin_id, db)


@router.put("/{checkin_id}", response_model=CheckinOut)
async def update_checkin(
    checkin_id: UUID,
    payload: CheckinUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_checkin_by_id(user["id"], checkin_id, payload, db)


@router.delete("/{checkin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkin(
    checkin_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_checkin_by_id(user["id"], checkin_id, db)
    return None
