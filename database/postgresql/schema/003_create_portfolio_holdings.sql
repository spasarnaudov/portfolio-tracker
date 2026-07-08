CREATE TABLE portfolio_holdings (
    asset_id INTEGER PRIMARY KEY,
    quantity NUMERIC(18, 6) NOT NULL DEFAULT 0,

    CONSTRAINT fk_portfolio_holdings_asset
        FOREIGN KEY (asset_id)
        REFERENCES assets(id)
        ON DELETE CASCADE
);
