from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Focus Journal"
    ENVIRONMENT: str = "production"
    DATABASE_URL: str

    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SESSION_SECRET_KEY: str
    SESSION_COOKIE_SECURE: bool = True

    CORS_ORIGINS: str = (
        "https://focus-journal-frontend.vercel.app,http://localhost:5173"
    )
    FRONTEND_BASE_URL: str = "https://focus-journal-frontend.vercel.app"

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_CALLBACK_URL: str | None = None
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    LINKEDIN_CLIENT_ID: str | None = None
    LINKEDIN_CLIENT_SECRET: str | None = None
    LINKEDIN_CALLBACK_URL: str | None = None
    LINKEDIN_SCOPE: str = "openid profile email"

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    @field_validator("SECRET_KEY", "SESSION_SECRET_KEY")
    @classmethod
    def validate_secret_length(cls, value: str) -> str:
        if len(value.strip()) < 32:
            raise ValueError("Secrets must be at least 32 characters long")
        return value

    @field_validator(
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_CALLBACK_URL",
        "GITHUB_CLIENT_ID",
        "GITHUB_CLIENT_SECRET",
        "LINKEDIN_CLIENT_ID",
        "LINKEDIN_CLIENT_SECRET",
        "LINKEDIN_CALLBACK_URL",
        "OPENAI_API_KEY",
    )
    @classmethod
    def normalize_optional_credentials(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
