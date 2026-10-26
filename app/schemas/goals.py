from pydantic import BaseModel, Field, field_validator


class GoalInout(BaseModel):
    goal: str = Field(..., min_length=5, max_length=200)
    target_days: int = Field(..., ge=1, le=7)

    @field_validator("goal")
    @classmethod
    def normalize_goal(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 5:
            raise ValueError("Goal must contain at least five non-space characters")
        return cleaned
