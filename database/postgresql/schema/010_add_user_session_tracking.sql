ALTER TABLE users
    ADD COLUMN IF NOT EXISTS active_session_token TEXT;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS active_session_expires_at TIMESTAMP;
