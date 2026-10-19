from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.tables import Tables
from schemas.focus_sessions import FocusSessionCreate

tables = Tables()
ACTIVE_STATUSES = ("running", "paused")


def calculate_elapsed_seconds(session: dict[str, Any], now: datetime | None = None) -> int:
    started_at = session["started_at"]
    end_at = session.get("ended_at") or session.get("paused_at") or now
    if end_at is None:
        end_at = datetime.now(timezone.utc)
    paused_seconds = int(session.get("paused_seconds") or 0)
    total = int((end_at - started_at).total_seconds()) - paused_seconds
    return max(0, total)


def serialize_focus_session(row: Any, now: datetime | None = None) -> dict[str, Any]:
    session = dict(row)
    session["elapsed_seconds"] = calculate_elapsed_seconds(session, now=now)
    return session


async def create_focus_session(
    user_id: UUID,
    payload: FocusSessionCreate,
    db: AsyncSession,
) -> dict:
    session_table = tables.focus_sessions
    active = await db.execute(
        select(session_table.c.id).where(
            session_table.c.user_id == user_id,
            session_table.c.status.in_(ACTIVE_STATUSES),
        )
    )
    if active.first():
        raise HTTPException(
            status_code=409,
            detail="Finish or abandon your active focus session before starting another",
        )

    now = datetime.now(timezone.utc)
    values = {
        "user_id": user_id,
        "title": payload.title,
        "status": "running",
        "planned_duration_seconds": (
            payload.planned_duration_minutes * 60
            if payload.planned_duration_minutes is not None
            else None
        ),
        "started_at": now,
        "created_at": now,
        "updated_at": now,
    }
    try:
        result = await db.execute(
            insert(session_table).values(**values).returning(session_table)
        )
        await db.commit()
        return serialize_focus_session(result.mappings().one(), now=now)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A focus session is already active",
        ) from None


async def list_focus_sessions(
    user_id: UUID,
    db: AsyncSession,
    *,
    limit: int,
    offset: int,
) -> dict:
    session_table = tables.focus_sessions
    result = await db.execute(
        select(session_table)
        .where(session_table.c.user_id == user_id)
        .order_by(session_table.c.started_at.desc())
        .limit(limit + 1)
        .offset(offset)
    )
    rows = result.mappings().all()
    has_more = len(rows) > limit
    now = datetime.now(timezone.utc)
    return {
        "items": [serialize_focus_session(row, now=now) for row in rows[:limit]],
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }


async def get_focus_session(
    user_id: UUID,
    session_id: UUID,
    db: AsyncSession,
) -> dict:
    session_table = tables.focus_sessions
    result = await db.execute(
        select(session_table).where(
            session_table.c.id == session_id,
            session_table.c.user_id == user_id,
        )
    )
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Focus session not found")
    return serialize_focus_session(row)


async def transition_focus_session(
    user_id: UUID,
    session_id: UUID,
    action: str,
    db: AsyncSession,
) -> dict:
    session_table = tables.focus_sessions
    try:
        result = await db.execute(
            select(session_table)
            .where(
                session_table.c.id == session_id,
                session_table.c.user_id == user_id,
            )
            .with_for_update()
        )
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="Focus session not found")

        current_status = row["status"]
        now = datetime.now(timezone.utc)
        values: dict[str, Any] = {"updated_at": now}

        if action == "pause":
            if current_status != "running":
                raise HTTPException(status_code=409, detail="Only a running session can be paused")
            values.update(status="paused", paused_at=now)
        elif action == "resume":
            if current_status != "paused":
                raise HTTPException(status_code=409, detail="Only a paused session can be resumed")
            paused_at = row["paused_at"]
            paused_total = int(row["paused_seconds"] or 0)
            if paused_at is not None:
                paused_total += max(0, int((now - paused_at).total_seconds()))
            values.update(status="running", paused_at=None, paused_seconds=paused_total)
        elif action in ("complete", "abandon"):
            if current_status not in ACTIVE_STATUSES:
                raise HTTPException(
                    status_code=409,
                    detail="Only an active session can be completed or abandoned",
                )
            paused_total = int(row["paused_seconds"] or 0)
            if current_status == "paused" and row["paused_at"] is not None:
                paused_total += max(0, int((now - row["paused_at"]).total_seconds()))
            values.update(
                status="completed" if action == "complete" else "abandoned",
                ended_at=now,
                paused_at=None,
                paused_seconds=paused_total,
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported focus-session action")

        updated = await db.execute(
            update(session_table)
            .where(
                session_table.c.id == session_id,
                session_table.c.user_id == user_id,
            )
            .values(**values)
            .returning(session_table)
        )
        updated_row = updated.mappings().one()
        await db.commit()
        return serialize_focus_session(updated_row, now=now)
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Focus session state conflict") from None


async def summarize_focus_sessions(
    user_id: UUID,
    db: AsyncSession,
    *,
    start_date: date,
    end_date: date,
    timezone_name: str,
) -> dict:
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")

    start_at = datetime.combine(start_date, time.min, tzinfo=zone).astimezone(timezone.utc)
    end_at = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=zone).astimezone(timezone.utc)
    session_table = tables.focus_sessions
    result = await db.execute(
        select(session_table)
        .where(
            session_table.c.user_id == user_id,
            session_table.c.status == "completed",
            session_table.c.started_at >= start_at,
            session_table.c.started_at < end_at,
        )
        .order_by(session_table.c.started_at.asc())
    )
    rows = result.mappings().all()
    elapsed_values = [
        calculate_elapsed_seconds(dict(row))
        for row in rows
    ]
    total_seconds = sum(elapsed_values)
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "completed_sessions": len(rows),
        "total_focus_seconds": total_seconds,
        "average_session_seconds": round(total_seconds / len(rows)) if rows else 0,
    }
