-- Recovery migration for databases previously started with the old migration
-- runner, which could skip migrations without recording their execution.
-- This file deliberately makes the core schema additions idempotent.
ALTER TABLE journal_entries
    ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE journal_entries
    ADD COLUMN IF NOT EXISTS tags TEXT[] NOT NULL DEFAULT '{}';
UPDATE journal_entries SET is_favorite = FALSE WHERE is_favorite IS NULL;
UPDATE journal_entries SET tags = '{}' WHERE tags IS NULL;
ALTER TABLE journal_entries ALTER COLUMN is_favorite SET DEFAULT FALSE;
ALTER TABLE journal_entries ALTER COLUMN is_favorite SET NOT NULL;
ALTER TABLE journal_entries ALTER COLUMN tags SET DEFAULT '{}';
ALTER TABLE journal_entries ALTER COLUMN tags SET NOT NULL;
CREATE INDEX IF NOT EXISTS ix_journal_entries_user_created_at
    ON journal_entries(user_id, created_at DESC);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) NOT NULL DEFAULT 'UTC';
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS ai_processing_consent BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    goal TEXT NOT NULL,
    target_days INT NOT NULL CHECK (target_days BETWEEN 1 AND 7),
    completed_days INT NOT NULL DEFAULT 0 CHECK (completed_days >= 0),
    status TEXT NOT NULL DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'failed')),
    created_at DATE NOT NULL DEFAULT CURRENT_DATE
);
CREATE INDEX IF NOT EXISTS ix_goals_user_created
    ON goals(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS focus_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL DEFAULT 'Focus session',
    status VARCHAR(20) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'paused', 'completed', 'abandoned')),
    planned_duration_seconds INTEGER
        CHECK (planned_duration_seconds IS NULL OR planned_duration_seconds > 0),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,
    paused_at TIMESTAMPTZ,
    paused_seconds INTEGER NOT NULL DEFAULT 0 CHECK (paused_seconds >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_focus_session_finished_state CHECK (
        (status IN ('running', 'paused') AND ended_at IS NULL)
        OR (status IN ('completed', 'abandoned') AND ended_at IS NOT NULL)
    ),
    CONSTRAINT ck_focus_session_pause_state CHECK (
        (status = 'paused' AND paused_at IS NOT NULL)
        OR (status <> 'paused' AND paused_at IS NULL)
    )
);
CREATE INDEX IF NOT EXISTS ix_focus_sessions_user_started
    ON focus_sessions(user_id, started_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_focus_sessions_one_active_per_user
    ON focus_sessions(user_id)
    WHERE status IN ('running', 'paused');
