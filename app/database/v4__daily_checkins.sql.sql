CREATE TABLE IF NOT EXISTS daily_checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    date DATE NOT NULL,  -- The calendar date of the check-in
    mood TEXT CHECK (mood IN ('bad', 'okay', 'good', 'great', 'happy')) NOT NULL,
    focus_percent INT CHECK (focus_percent >= 0 AND focus_percent <= 100),
    tags TEXT[], -- Optional user-defined tags (like #productive, #tired)
    note TEXT,   -- Optional reflection
    sleep_duration NUMERIC CHECK (sleep_duration >= 0 AND sleep_duration <= 24),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(user_id, date), -- One check-in per user per day

    CONSTRAINT fk_user_checkin FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_checkin_user_date ON daily_checkins(user_id, date);
CREATE INDEX IF NOT EXISTS idx_checkin_mood ON daily_checkins(mood);
CREATE INDEX IF NOT EXISTS idx_checkin_focus ON daily_checkins(focus_percent);


CREATE TABLE IF NOT EXISTS user_streaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    current_streak INT DEFAULT 0, -- How many consecutive days user has checked in
    longest_streak INT DEFAULT 0, -- Max consecutive days ever
    last_checkin_date DATE,       -- Last check-in date for streak calculation
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT fk_user_streak FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index
CREATE INDEX IF NOT EXISTS idx_user_streak_userid ON user_streaks(user_id);
