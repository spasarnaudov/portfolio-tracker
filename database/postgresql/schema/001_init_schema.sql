CREATE TABLE asset_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER NOT NULL,

    CONSTRAINT fk_assets_category
        FOREIGN KEY (category_id)
        REFERENCES asset_categories(id)
);

CREATE TABLE asset_prices (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    price_date TIMESTAMP NOT NULL,
    price NUMERIC(18, 6) NOT NULL,

    CONSTRAINT fk_asset_prices_asset
        FOREIGN KEY (asset_id)
        REFERENCES assets(id),

    CONSTRAINT uq_asset_price_per_date
        UNIQUE (asset_id, price_date)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    active_session_token TEXT,
    active_session_expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_users_role
        CHECK (role IN ('admin', 'user'))
);

CREATE UNIQUE INDEX uq_users_single_admin_role
    ON users(role)
    WHERE role = 'admin';

CREATE FUNCTION prevent_deleted_user_state_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_deleted
        AND NEW.is_deleted IS DISTINCT FROM OLD.is_deleted
    THEN
        RAISE EXCEPTION 'Deleted user state cannot be changed';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_deleted_user_state_change
BEFORE UPDATE OF is_deleted ON users
FOR EACH ROW
EXECUTE FUNCTION prevent_deleted_user_state_change();

CREATE TABLE user_login_history (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(100) NOT NULL,
    logged_in_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_login_history_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_user_login_history_user_date
    ON user_login_history(user_id, logged_in_at DESC);

CREATE TABLE portfolio_holdings (
    user_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    quantity NUMERIC(18, 6) NOT NULL DEFAULT 0,
    include_in_chart BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT portfolio_holdings_pkey
        PRIMARY KEY (user_id, asset_id),

    CONSTRAINT fk_portfolio_holdings_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_portfolio_holdings_asset
        FOREIGN KEY (asset_id)
        REFERENCES assets(id)
        ON DELETE CASCADE
);

CREATE TABLE portfolio_manual_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    quantity NUMERIC(18, 6) NOT NULL DEFAULT 0,
    unit_price NUMERIC(18, 6) NOT NULL DEFAULT 0,
    include_in_chart BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_portfolio_manual_items_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE portfolio_manual_item_prices (
    id SERIAL PRIMARY KEY,
    manual_item_id INTEGER NOT NULL,
    price_date TIMESTAMP NOT NULL,
    price NUMERIC(18, 6) NOT NULL,

    CONSTRAINT fk_portfolio_manual_item_prices_item
        FOREIGN KEY (manual_item_id)
        REFERENCES portfolio_manual_items(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_portfolio_manual_item_price_per_date
        UNIQUE (manual_item_id, price_date)
);

CREATE INDEX idx_portfolio_holdings_user_id
    ON portfolio_holdings(user_id);

CREATE INDEX idx_portfolio_manual_items_user_id
    ON portfolio_manual_items(user_id);

CREATE INDEX idx_portfolio_manual_item_prices_item_date
    ON portfolio_manual_item_prices(manual_item_id, price_date);
