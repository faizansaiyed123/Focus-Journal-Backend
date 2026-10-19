# Focus Journal Backend

FastAPI and PostgreSQL backend for private journaling, daily reflection, and focused-work sessions.

The product scope is intentionally focused on one useful daily loop: start a focus session, record a short check-in, write a journal entry, and review saved history. Billing, unrelated trackers, reminders, and unimplemented premium features are deferred.

See app/README.md for configuration, API contracts, migrations, testing, and deployment.

## Security

Do not commit environment files. Rotate credentials that may remain in Git history even after local environment files are removed. Deploy the backend and frontend's one-time OAuth code exchange together.
