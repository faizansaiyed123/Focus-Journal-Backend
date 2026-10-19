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
