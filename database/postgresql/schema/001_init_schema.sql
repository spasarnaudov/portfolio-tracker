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
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    active_session_token TEXT,
    active_session_expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_users_role
        CHECK (role IN ('admin', 'user', 'demo'))
);

CREATE TABLE portfolio_holdings (
    user_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    quantity NUMERIC(18, 6) NOT NULL DEFAULT 0,

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

    CONSTRAINT fk_portfolio_manual_items_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_portfolio_holdings_user_id
    ON portfolio_holdings(user_id);

CREATE INDEX idx_portfolio_manual_items_user_id
    ON portfolio_manual_items(user_id);
