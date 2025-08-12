from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from api.routes import (
    auth,
    github,
    google,
    linkedin,
    journal,
    checkin,
    analytics,
    insights,
    goals,
    journal_compare,
)
from core.config import settings

from db.table_creation_script import execute_sql_files
from db.tables import Tables
import nltk

tables = Tables()
app = FastAPI(title=settings.PROJECT_NAME)

# ✅ Startup event


@app.on_event("startup")
async def startup_event():
    await execute_sql_files()
    await tables.reflect_metadata()
    nltk.download("vader_lexicon")


# ✅ Middleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React app on port 3000 (adjust if needed)
        "http://localhost:5173",  # React app on port 5173 (your frontend)
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    same_site="lax",
    https_only=False,
    max_age=3600,
)

# ✅ Routes
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


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Focus API",
        version="1.0.0",
        description="Secure JWT-authenticated API",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {"type": "http", "scheme": "bearer"}
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"HTTPBearer": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
