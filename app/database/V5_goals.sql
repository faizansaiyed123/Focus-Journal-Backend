CREATE TABLE goals (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),  -- Assumes a 'users' table exists
    goal TEXT NOT NULL,
    target_days INT NOT NULL,
    completed_days INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed', 'failed')),
    created_at DATE NOT NULL DEFAULT CURRENT_DATE
);
