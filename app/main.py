from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from api.routes import (
    analytics,
    auth,
    checkin,
    focus_sessions,
    github,
    google,
    goals,
    insights,
    journal,
    journal_compare,
    linkedin,
    profile,
)
from core.config import settings
from db.session import engine
from db.table_creation_script import execute_sql_files
from db.tables import Tables

tables = Tables()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await execute_sql_files()
    await tables.reflect_metadata()
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.1.0",
    description=(
        "Focus Journal API for private journaling, daily reflection and focus sessions."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    same_site="lax",
    https_only=settings.SESSION_COOKIE_SECURE,
    max_age=600,
    session_cookie="focus_journal_session",
)

app.include_router(auth.router)
app.include_router(github.router)
app.include_router(google.router)
app.include_router(linkedin.router)
app.include_router(journal.router)
app.include_router(checkin.router)
app.include_router(analytics.router)
app.include_router(insights.router)
app.include_router(goals.router)
app.include_router(journal_compare.router)
app.include_router(profile.router)
app.include_router(focus_sessions.router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
