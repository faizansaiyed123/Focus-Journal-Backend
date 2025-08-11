from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi.security import HTTPBearer


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "Focus Journal"
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    JWT_EXPIRY_MINUTES: int = 60
    DATABASE_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_CALLBACK_URL: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    LINKEDIN_CLIENT_ID: str
    LINKEDIN_CLIENT_SECRET: str
    LINKEDIN_CALLBACK_URL: str
    SESSION_SECRET_KEY:str
    LINKEDIN_SCOPE:str
    OPENAI_API_KEY: str


settings = Settings()
oauth2_scheme = HTTPBearer()
