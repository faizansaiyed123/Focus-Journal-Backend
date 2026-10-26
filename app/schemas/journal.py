from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JournalEntryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=50000)
    mood: str | None = Field(default=None, max_length=50)
    is_favorite: bool = False
    focus_percent: int | None = Field(default=None, ge=0, le=100)
    tags: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Title must not be blank")
        return cleaned

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


class JournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str | None = None
    mood: str | None = None
    focus_percent: int | None = None
    is_favorite: bool = False
    tags: list[str] = Field(default_factory=list)
    created_at: datetime


class UpdateJournalEntry(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=50000)
    mood: str | None = Field(default=None, max_length=50)
    focus_percent: int | None = Field(default=None, ge=0, le=100)
    is_favorite: bool | None = None
    tags: list[str] | None = Field(default=None, max_length=30)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Title must not be blank")
        return cleaned

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
