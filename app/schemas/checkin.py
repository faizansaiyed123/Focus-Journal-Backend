from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Mood = Literal["bad", "okay", "good", "great", "happy"]


class CheckinBase(BaseModel):
    checkin_date: date = Field(
        ...,
        alias="date",
        description="Calendar date in YYYY-MM-DD format",
    )
    mood: Mood
    focus_percent: int = Field(..., ge=0, le=100)
    tags: list[str] = Field(default_factory=list, max_length=30)
    note: str | None = Field(default=None, max_length=10000)

    @field_validator("mood", mode="before")
    @classmethod
    def normalize_mood(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        cleaned = []
        seen = set()
        for item in value:
            tag = item.strip().lstrip("#").strip().lower()
            if tag and tag not in seen:
                if len(tag) > 50:
                    raise ValueError("Tags must be 50 characters or fewer")
                cleaned.append(tag)
                seen.add(tag)
        return cleaned


class CheckinCreate(CheckinBase):
    pass


class CheckinUpdate(BaseModel):
    mood: Mood | None = None
    focus_percent: int | None = Field(default=None, ge=0, le=100)
    tags: list[str] | None = Field(default=None, max_length=30)
    note: str | None = Field(default=None, max_length=10000)

    @field_validator("mood", mode="before")
    @classmethod
    def normalize_mood(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = []
        seen = set()
        for item in value:
            tag = item.strip().lstrip("#").strip().lower()
            if tag and tag not in seen:
                if len(tag) > 50:
                    raise ValueError("Tags must be 50 characters or fewer")
                cleaned.append(tag)
                seen.add(tag)
        return cleaned


class CheckinOut(CheckinBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class StreakOut(BaseModel):
    user_id: UUID
    current_streak: int = Field(..., ge=0)
    longest_streak: int = Field(..., ge=0)
    last_checkin_date: date | None = None
