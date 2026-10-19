# Focus Journal API

Focus Journal is a focused personal tool for journal entries, one short daily check-in, intentional focus sessions, and simple history-based review. Billing, reminders, unrelated trackers, and speculative AI coaching are deferred.

## Stack

- Python 3.12, FastAPI, and Pydantic
- PostgreSQL, SQLAlchemy async sessions, and asyncpg
- JWT bearer authentication with short-lived OAuth code exchange
- Optional Google, GitHub, and LinkedIn OAuth
- Optional OpenAI journal insights, gated by explicit per-user consent

## Local configuration

From the repository root, copy the example configuration into the ignored app configuration file:

    cp .env.example app/.env

Generate independent secrets with:

    python -c "import secrets; print(secrets.token_urlsafe(48))"

Replace the example SECRET_KEY and SESSION_SECRET_KEY with separately generated values. Both must be at least 32 characters. Set SESSION_COOKIE_SECURE=false only for local HTTP development; keep it enabled in HTTPS deployments.

Configure DATABASE_URL and CORS_ORIGINS for your environment. Configure OAuth and OpenAI credentials only when enabling those integrations.

## Run locally

    cd app
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt -r requirements-dev.txt
    uvicorn main:app --reload

Migrations are applied on startup and schema metadata is reflected afterward. Migration attempts use a PostgreSQL advisory lock and are recorded only after successful execution. For scaled production deployments, run migrations as a single deployment step before scaling API workers.

## Main API

All private endpoints require Authorization: Bearer token.

| Area | Routes |
|---|---|
| Authentication | POST /auth/register, POST /auth/login, POST /auth/exchange, GET /auth/me |
| Journal | POST/GET /journal/, GET/PUT/DELETE /journal/{id}, GET /journal/stats |
| Check-ins | POST/GET /checkin/, GET /checkin/today, GET /checkin/stats, GET /checkin/streak, GET/PUT/DELETE by id |
| Search and calendar | GET /checkin/journal/search?keyword=..., GET /checkin/journal/tags, GET /checkin/journal/calendar |
| Focus sessions | POST/GET /focus-sessions/, GET /focus-sessions/{id}, POST pause/resume/complete/abandon actions, GET /focus-sessions/summary |
| Profile and privacy | GET /profile, PATCH /profile/settings |
| Summary | GET /weekly-summary, GET /monthly-summary, GET /tag-summary, POST /journal/compare |
| Health | GET /health |

The old /checkin/checkin/today, /checkin/checkin/stats and /checkin/checkin/history paths remain as hidden compatibility aliases.

## Product contracts

- A journal entry is free-form writing; a daily check-in is a separate structured record.
- A check-in is unique per user-local date. Mood values and tags are normalized by the API.
- Streak calculations derive from saved check-in dates.
- A user may have only one active focus session. Paused time does not count toward elapsed focus time.
- User timezone is an IANA timezone stored in profile settings.
- AI insights return 403 until a user opts into AI processing, and 503 when the provider is not configured.
- Summaries use saved data. Empty history does not create fabricated scores.

## OAuth security and deployment

OAuth redirects use a high-entropy single-use code instead of a bearer token. The code is stored only as a SHA-256 digest, expires after two minutes, and is atomically consumed by POST /auth/exchange. The frontend removes the code from its callback URL immediately and exchanges it for an access token over HTTPS. Deploy the frontend and backend changes together.

Previously deployed databases may contain secrets or partially applied schemas. Rotate credentials that have appeared in repository history. Before applying migrations to valuable production data, take a backup and test against a restored copy. Provide secrets through deployment environment variables; Docker images must not contain .env.

## Tests

    pip install -r requirements.txt -r requirements-dev.txt
    pytest -q

CI runs against a disposable PostgreSQL service. Tests need no live OAuth provider or AI credentials. The Docker build installs the NLTK VADER lexicon; local sentiment-analysis environments should install that resource before use.
