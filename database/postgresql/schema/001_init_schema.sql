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

CREATE TABLE portfolio_holdings (
    asset_id INTEGER PRIMARY KEY,
    quantity NUMERIC(18, 6) NOT NULL DEFAULT 0,

    CONSTRAINT fk_portfolio_holdings_asset
        FOREIGN KEY (asset_id)
        REFERENCES assets(id)
        ON DELETE CASCADE
);

CREATE TABLE portfolio_manual_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    quantity NUMERIC(18, 6) NOT NULL DEFAULT 0,
    unit_price NUMERIC(18, 6) NOT NULL DEFAULT 0
);

CREATE TABLE portfolio_cash_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    amount NUMERIC(18, 6) NOT NULL DEFAULT 0
);
