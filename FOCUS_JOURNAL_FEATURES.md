# Focus Journal: Product Scope

This file is a scope contract, not a list of aspirational features. A feature is not "implemented" unless its route, validation, persistence, ownership checks, and tests agree.

## Core daily loop

1. Start an intentional focus session and track running, paused, completed, or abandoned state.
2. Record one short structured check-in per local calendar day.
3. Write and organize longer journal entries independently from check-ins.
4. Review real saved history and basic aggregates.
5. Keep profile settings and private journal content under user control.

## Included backend behavior

- Password registration/login and JWT authentication.
- Optional Google, GitHub and LinkedIn sign-in when configured.
- Owner-scoped journal CRUD, normalized tags, favorites, search and entry statistics.
- One local-date daily check-in, editable history, and streak calculation from check-in dates.
- Calendar aggregation that labels journal entries separately from check-ins.
- Focus sessions with state transitions, elapsed-time calculation excluding pauses, one-active-session enforcement, history pagination, and date-range summaries.
- Profile timezone and explicit consent flag for any AI journal processing.
- Optional AI-generated journal insights only after consent; provider failures fail closed.
- Ordered, recorded SQL migrations and PostgreSQL-backed API tests.

## Explicitly deferred

These are not current product promises and must not be represented as working features:

- Stripe/subscription billing or premium entitlements.
- Email digests, reminders, push notifications or background jobs.
- Standalone habit, gratitude, energy, distraction and multiple daily trackers.
- AI coaching/chatrooms, automatic tagging, and generated weekly/monthly prose reviews.
- A separate full project/task manager; focus-session title is enough for current intent.
- Goal progress claims until there is an explicit, honest progress-recording workflow.

Only revisit deferred ideas when there is a clear user problem and the whole workflow can be designed and tested end to end.
