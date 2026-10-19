# Focus Journal Backend

FastAPI and PostgreSQL backend for private journaling, daily reflection, and focused-work sessions.

The product scope is intentionally focused on one useful daily loop: start a focus session, record a short check-in, write a journal entry, and review actual saved history. Billing, unrelated trackers, reminders, and unimplemented premium features are deferred.

See app/README.md for local configuration, API contracts, migration behavior, testing, and deployment.

## Security

Do not commit environment files. If credentials have ever been committed, rotate them at the provider and deployment platform; deleting a file in a later commit does not remove earlier history. Before production use, also complete the documented one-time OAuth code exchange with the frontend so browser history does not retain access tokens.
