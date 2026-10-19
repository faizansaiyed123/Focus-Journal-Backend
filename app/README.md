# Focus Journal API

Focus Journal is a focused personal tool for journal entries, one short daily check-in, intentional focus sessions, and simple history-based review. Keep the experience cohesive: billing, reminders, unrelated trackers, and speculative AI coaching are deferred.

## Stack

- Python 3.12
- FastAPI and Pydantic
- PostgreSQL, SQLAlchemy async sessions and asyncpg
- JWT bearer authentication
- Authlib OAuth integrations, enabled only when credentials are configured
- Optional OpenAI journal insights, gated by explicit per-user consent

## Local configuration

From the repository root, copy the example configuration into the ignored app configuration file:

    cp .env.example app/.env

Generate independent secrets with:

    python -c "import secrets; print(secrets.token_urlsafe(48))"

Replace the example SECRET_KEY and SESSION_SECRET_KEY with separately generated values. Both must be at least 32 characters. Set SESSION_COOKIE_SECURE=false only for local HTTP development; keep it enabled in HTTPS deployments.

Configure DATABASE_URL and CORS_ORIGINS for your local environment. Configure Google, GitHub, LinkedIn and OpenAI credentials only when enabling those integrations. They are optional for the core API and tests.

## Run locally

    cd app
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt -r requirements-dev.txt
    uvicorn main:app --reload

Migrations are applied on startup and schema metadata is reflected afterward. The migration runner serializes migration attempts using a PostgreSQL advisory lock and records only successful scripts. For scaled production deployments, run migrations as a single deployment step before scaling API workers.

## Main API

All private endpoints require Authorization: Bearer token.

| Area | Routes |
|---|---|
| Authentication | POST /auth/register, POST /auth/login, GET /auth/me |
| Journal | POST/GET /journal/, GET/PUT/DELETE /journal/{id}, GET /journal/stats |
| Check-ins | POST/GET /checkin/, GET /checkin/today, GET /checkin/stats, GET /checkin/streak, GET/PUT/DELETE by id |
| Search and calendar | GET /checkin/journal/search?keyword=..., GET /checkin/journal/tags, GET /checkin/journal/calendar |
| Focus sessions | POST/GET /focus-sessions/, GET /focus-sessions/{id}, POST pause/resume/complete/abandon actions, GET /focus-sessions/summary |
| Profile and privacy | GET /profile, PATCH /profile/settings |
| Summary | GET /weekly-summary, GET /monthly-summary, GET /tag-summary, POST /journal/compare |
| Health | GET /health |

The older /checkin/checkin/today, /checkin/checkin/stats and /checkin/checkin/history paths remain as hidden aliases while the existing frontend is being integrated with the canonical paths.

## Product contracts

- A journal entry is free-form writing. A daily check-in is a separate structured record; both can appear in calendar history and search remains focused on journal entries.
- A check-in is unique per user-local date. Mood values are normalized and checked by the API and database.
- Streak calculations derive from saved check-in dates instead of a separately maintained counter.
- Only one focus session per user may be active (running or paused). A session supports running to paused to running to completed/abandoned transitions. Elapsed time comes from server timestamps and excludes recorded pauses.
- User timezone is an IANA timezone stored in profile settings.
- AI insights return 403 unless the user explicitly enables AI processing; if the provider is not configured they return 503. A consent/settings experience must be added to the frontend before re-exposing this feature.
- Weekly and monthly summaries return actual saved data. Missing history is represented as an empty result, not invented scores.

## Migrations and existing databases

The SQL files are ordered by the numeric migration prefix. The V8 recovery migration repairs core columns idempotently for databases whose older migration runner skipped a file without recording it. Do not manually delete migration records.

Previously deployed databases may already contain secrets or a partially applied schema. Rotate credentials that may have appeared in repository history. Before applying this version to valuable production data, take a database backup and test the migrations against a restore of the existing schema.

## Tests

    pip install -r requirements.txt -r requirements-dev.txt
    pytest -q

The GitHub Actions workflow runs against a disposable PostgreSQL service. Tests require no live OAuth provider or AI credentials. The Docker build installs the NLTK VADER lexicon during image construction; local installations that use sentiment analysis should install that resource before calling the sentiment endpoint.

## Deployment notes

- Use the root Dockerfile with repository root as build context, or app/Dockerfile with app/ as build context.
- Provide environment variables through the deployment platform; Docker intentionally does not copy environment files.
- Keep cookie Secure enabled for HTTPS and restrict CORS to exact frontend origins.
- OAuth redirects still deliver the legacy access token in the query string to preserve the currently deployed frontend. This remains a security limitation until the frontend adopts a one-time authorization-code exchange; do not consider the full application production-ready until that cross-repository integration is completed.
