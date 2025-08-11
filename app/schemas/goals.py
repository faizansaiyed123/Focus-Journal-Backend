from pydantic import BaseModel, Field


class GoalInout(BaseModel):
    goal: str = Field(..., min_length=5)
    target_days: int = Field(..., gt=0, le=7)
