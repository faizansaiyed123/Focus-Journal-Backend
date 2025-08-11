-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR NOT NULL UNIQUE,
    password VARCHAR,
    
    -- OAuth fields
    google_id VARCHAR UNIQUE,
    linkedin_id VARCHAR UNIQUE,
    github_id VARCHAR UNIQUE,

    full_name VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

-- Add indexes separately if needed (some ORMs do this)
CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

-- Create the password_reset_tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token VARCHAR UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add index to foreign key for performance
CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id ON password_reset_tokens (user_id);
