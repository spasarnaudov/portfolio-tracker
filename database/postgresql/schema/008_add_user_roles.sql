ALTER TABLE users
    ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_users_role'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT ck_users_role
            CHECK (role IN ('admin', 'user', 'demo'));
    END IF;
END $$;

UPDATE users
SET role = 'admin'
WHERE LOWER(username) = LOWER('spas');

UPDATE users
SET role = 'demo'
WHERE LOWER(username) = LOWER('demo');
