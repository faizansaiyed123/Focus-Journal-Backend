from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileSettingsUpdate(BaseModel):
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    ai_processing_consent: bool | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Timezone must be a valid IANA timezone name") from None
        return value


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str | None = None
    timezone: str = "UTC"
    ai_processing_consent: bool = False
