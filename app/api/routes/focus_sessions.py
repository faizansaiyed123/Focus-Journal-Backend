from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user
from db.session import get_db
from schemas.focus_sessions import (
    FocusSessionCreate,
    FocusSessionListResponse,
    FocusSessionResponse,
    FocusSessionSummaryResponse,
)
from services.focus_sessions import (
    create_focus_session,
    get_focus_session,
    list_focus_sessions,
    summarize_focus_sessions,
    transition_focus_session,
)
from utils.dates import user_local_today

router = APIRouter(prefix="/focus-sessions", tags=["Focus sessions"])


@router.post("/", response_model=FocusSessionResponse, status_code=201)
async def start_focus_session(
    payload: FocusSessionCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_focus_session(user["id"], payload, db)


@router.get("/", response_model=FocusSessionListResponse)
async def get_focus_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_focus_sessions(user["id"], db, limit=limit, offset=offset)


@router.get("/summary", response_model=FocusSessionSummaryResponse)
async def focus_session_summary(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = user_local_today(user)
    resolved_end = end_date or today
    resolved_start = start_date or (resolved_end - timedelta(days=6))
    return await summarize_focus_sessions(
        user["id"],
        db,
        start_date=resolved_start,
        end_date=resolved_end,
        timezone_name=user.get("timezone") or "UTC",
    )


@router.get("/{session_id}", response_model=FocusSessionResponse)
async def focus_session_detail(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_focus_session(user["id"], session_id, db)


@router.post("/{session_id}/pause", response_model=FocusSessionResponse)
async def pause_focus_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await transition_focus_session(user["id"], session_id, "pause", db)


@router.post("/{session_id}/resume", response_model=FocusSessionResponse)
async def resume_focus_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await transition_focus_session(user["id"], session_id, "resume", db)


@router.post("/{session_id}/complete", response_model=FocusSessionResponse)
async def complete_focus_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await transition_focus_session(user["id"], session_id, "complete", db)


@router.post("/{session_id}/abandon", response_model=FocusSessionResponse)
async def abandon_focus_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await transition_focus_session(user["id"], session_id, "abandon", db)
