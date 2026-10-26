from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

FocusSessionStatus = Literal["running", "paused", "completed", "abandoned"]


class FocusSessionCreate(BaseModel):
    title: str = Field(default="Focus session", min_length=1, max_length=200)
    planned_duration_minutes: int | None = Field(default=None, ge=1, le=480)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Title must not be blank")
        return cleaned


class FocusSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    status: FocusSessionStatus
    planned_duration_seconds: int | None = None
    started_at: datetime
    ended_at: datetime | None = None
    paused_at: datetime | None = None
    paused_seconds: int = 0
    elapsed_seconds: int = Field(..., ge=0)
    created_at: datetime
    updated_at: datetime


class FocusSessionListResponse(BaseModel):
    items: list[FocusSessionResponse]
    limit: int
    offset: int
    has_more: bool


class FocusSessionSummaryResponse(BaseModel):
    start_date: str
    end_date: str
    completed_sessions: int
    total_focus_seconds: int
    average_session_seconds: int
