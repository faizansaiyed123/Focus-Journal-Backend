CREATE TABLE IF NOT EXISTS oauth_login_codes (
    code_hash CHAR(64) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    CONSTRAINT ck_oauth_login_codes_expiry CHECK (expires_at > created_at)
);

CREATE INDEX IF NOT EXISTS ix_oauth_login_codes_expiry
ON oauth_login_codes(expires_at);
