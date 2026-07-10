DO $$
DECLARE
    owner_user_id INTEGER;
BEGIN
    SELECT id
    INTO owner_user_id
    FROM users
    WHERE LOWER(username) = LOWER('spas');

    IF owner_user_id IS NULL THEN
        RAISE EXCEPTION 'Create user spas before running this migration.';
    END IF;

    ALTER TABLE portfolio_holdings
        ADD COLUMN IF NOT EXISTS user_id INTEGER;

    ALTER TABLE portfolio_manual_items
        ADD COLUMN IF NOT EXISTS user_id INTEGER;

    ALTER TABLE portfolio_cash_items
        ADD COLUMN IF NOT EXISTS user_id INTEGER;

    UPDATE portfolio_holdings
    SET user_id = owner_user_id
    WHERE user_id IS NULL;

    UPDATE portfolio_manual_items
    SET user_id = owner_user_id
    WHERE user_id IS NULL;

    UPDATE portfolio_cash_items
    SET user_id = owner_user_id
    WHERE user_id IS NULL;

    ALTER TABLE portfolio_holdings
        ALTER COLUMN user_id SET NOT NULL;

    ALTER TABLE portfolio_manual_items
        ALTER COLUMN user_id SET NOT NULL;

    ALTER TABLE portfolio_cash_items
        ALTER COLUMN user_id SET NOT NULL;

    ALTER TABLE portfolio_holdings
        DROP CONSTRAINT IF EXISTS portfolio_holdings_pkey;

    ALTER TABLE portfolio_holdings
        ADD CONSTRAINT portfolio_holdings_pkey
        PRIMARY KEY (user_id, asset_id);

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_portfolio_holdings_user'
    ) THEN
        ALTER TABLE portfolio_holdings
            ADD CONSTRAINT fk_portfolio_holdings_user
            FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_portfolio_manual_items_user'
    ) THEN
        ALTER TABLE portfolio_manual_items
            ADD CONSTRAINT fk_portfolio_manual_items_user
            FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_portfolio_cash_items_user'
    ) THEN
        ALTER TABLE portfolio_cash_items
            ADD CONSTRAINT fk_portfolio_cash_items_user
            FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_user_id
    ON portfolio_holdings(user_id);

CREATE INDEX IF NOT EXISTS idx_portfolio_manual_items_user_id
    ON portfolio_manual_items(user_id);

CREATE INDEX IF NOT EXISTS idx_portfolio_cash_items_user_id
    ON portfolio_cash_items(user_id);
