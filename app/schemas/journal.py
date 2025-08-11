from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class JournalEntryCreate(BaseModel):
    title: str
    content: Optional[str] = None
    mood: Optional[str] = None
    is_favorite: Optional[bool] = False
    focus_percent: Optional[int] = Field(default=None, ge=0, le=100)
    tags: Optional[List[str]] = Field(default_factory=list)


class JournalEntryResponse(BaseModel):
    id: UUID
    title: str
    content: Optional[str]
    mood: Optional[str]
    focus_percent: Optional[int]
    is_favorite: Optional[bool] = False
    tags: Optional[List[str]] = Field(default_factory=list)
    created_at: datetime


class UpdateJournalEntry(BaseModel):
    title: Optional[str]
    content: Optional[str]
    mood: Optional[str]
    focus_percent: Optional[int]
    is_favorite: Optional[bool]
    tags: Optional[List[str]] = Field(default_factory=list)

    class Config:
        from_attributes = True
