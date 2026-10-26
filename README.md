# Focus Journal — Backend

FastAPI and PostgreSQL API for Focus Journal, a personal journaling and focused-work application. The backend supports private journal entries, structured daily check-ins, focus sessions, saved-history summaries, and optional AI-assisted insights.

**Frontend:** https://github.com/faizansaiyed123/Focus-Journal-Frontend

## Core functionality

- Account registration, authentication, and single-use OAuth code exchange
- Private journal entry CRUD and saved-history review
- Daily check-ins, mood and tag normalization, streaks, and calendar/search routes
- Focus-session lifecycle, including pause, resume, completion, and abandonment
- Profile preferences and privacy settings
- Weekly, monthly, and tag summaries
- Optional AI journal insights, available only with explicit user consent

## Technology

- Python 3.12, FastAPI, and Pydantic
- PostgreSQL, SQLAlchemy async sessions, and asyncpg
- JWT bearer authentication and short-lived OAuth exchange codes
- Optional Google, GitHub, and LinkedIn OAuth integrations
- Optional OpenAI-powered journal insights

## Local setup

Create a local environment file from the example configuration:

```bash
cp .env.example app/.env
```

Generate independent values for SECRET_KEY and SESSION_SECRET_KEY:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Use a different generated value for each secret. Configure DATABASE_URL, CORS_ORIGINS, and FRONTEND_BASE_URL for your environment. OAuth and AI credentials are needed only when enabling those integrations.

Run the API:

```bash
cd app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn main:app --reload
```

Use Python 3.12. For Windows, activate the virtual environment with .venv\Scripts\activate.

## API overview

Private routes require a valid bearer token.

| Area | Routes |
|---|---|
| Authentication | /auth/register, /auth/login, /auth/exchange, /auth/me |
| Journals | /journal/, /journal/{id}, /journal/stats |
| Check-ins | /checkin/, /checkin/today, /checkin/stats, /checkin/streak |
| Search and calendar | /checkin/journal/search, /checkin/journal/tags, /checkin/journal/calendar |
| Focus sessions | /focus-sessions/, /focus-sessions/{id}, /focus-sessions/summary |
| Profile and privacy | /profile, /profile/settings |
| Summaries | /weekly-summary, /monthly-summary, /tag-summary |
| Health | /health |

The detailed API contract, product behavior, migration notes, and local testing instructions are documented in [app/README.md](app/README.md).

## OAuth and deployment

OAuth uses a high-entropy, single-use code instead of putting a bearer token in the redirect URL. The code is stored as a SHA-256 digest, expires after two minutes, and is atomically consumed by POST /auth/exchange. Use HTTPS in deployed environments and deploy compatible frontend and backend versions together.

## Configuration and credential safety

- The tracked .env.example is a template; replace its placeholders locally and never use example secrets in production.
- Local environment files, database credentials, signing keys, OAuth client secrets, and provider API keys must not be committed.
- The repository's .gitignore excludes environment files while allowing example templates.
- Removing a credential from the latest files does not remove it from earlier Git commits. If a real credential was ever committed, revoke or rotate it at its provider and review repository history. Do not assume a file deletion makes a previously exposed secret safe.
- Configure production secrets through the deployment platform. Keep session cookies secure over HTTPS and restrict CORS to trusted frontend origins.

## Tests

```bash
cd app
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

CI uses a disposable PostgreSQL service. Tests do not require live OAuth-provider or AI credentials.
