import re

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    confirm_password: str = Field(min_length=8, max_length=72)
    full_name: str | None = Field(default=None, max_length=255, validation_alias=AliasChoices("full_name", "name"))

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        checks = (
            (r"[A-Z]", "at least one uppercase letter"),
            (r"[a-z]", "at least one lowercase letter"),
            (r"[0-9]", "at least one number"),
            (r'[!@#$%^&*(),.?":{}|<>]', "at least one special character"),
        )
        for pattern, message in checks:
            if not re.search(pattern, value):
                raise ValueError(f"Password must contain {message}")
        return value

    @field_validator("full_name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def passwords_must_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # Compatibility alias retained for older password-login clients.
    token: str | None = None


class OAuthCodeExchange(BaseModel):
    code: str = Field(min_length=32, max_length=128)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
