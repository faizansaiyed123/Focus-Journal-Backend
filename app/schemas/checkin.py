from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import date, datetime
from uuid import UUID


# ---------- Base Schema ----------
class CheckinBase(BaseModel):
    checkin_date: date = Field(
        ..., alias="date", description="Calendar date (YYYY-MM-DD)"
    )
    mood: str = Field(..., description="Mood must be one of: bad, okay, good, great")
    focus_percent: int = Field(
        ..., ge=0, le=100, description="Focus percentage (0 to 100)"
    )
    tags: Optional[List[str]] = Field(
        default=[], description="Optional list of user-defined tags"
    )
    note: Optional[str] = Field(default=None, description="Optional reflection note")


# ---------- Create Schema ----------
class CheckinCreate(CheckinBase):
    pass


# ---------- Update Schema ----------
class CheckinUpdate(BaseModel):
    mood: Optional[Literal["bad", "okay", "good", "great"]]
    focus_percent: Optional[int] = Field(ge=0, le=100)
    tags: Optional[List[str]]
    note: Optional[str]


# ---------- Output Schema ----------
class CheckinOut(CheckinBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class StreakOut(BaseModel):
    user_id: UUID = Field(..., description="User ID")
    current_streak: int = Field(..., ge=0, description="Current ongoing streak")
    longest_streak: int = Field(..., ge=0, description="Longest streak ever achieved")
    last_checkin_date: Optional[date] = Field(None, description="Date of last check-in")

    class Config:
        orm_mode = True
