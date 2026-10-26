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
