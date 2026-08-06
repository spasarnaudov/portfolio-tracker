-- One-off, hand-run migration for existing databases created before purchase
-- lots existed. Run once via psql, the same way as the maintenance/*.sql
-- scripts (see docs/database-operations.md). Fresh installs never need this
-- — schema/001_init_schema.sql already reflects the target shape.
--
-- Backfills one placeholder lot per existing holding (today's date, price 0)
-- so current quantities are preserved; edit each lot afterwards with the
-- real purchase price/date for accurate profit figures.

BEGIN;

CREATE TABLE portfolio_asset_purchases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    quantity NUMERIC(18, 6) NOT NULL,
    purchase_price NUMERIC(18, 6) NOT NULL,
    purchase_date TIMESTAMP NOT NULL,

    CONSTRAINT fk_portfolio_asset_purchases_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_portfolio_asset_purchases_asset
        FOREIGN KEY (asset_id)
        REFERENCES assets(id)
        ON DELETE CASCADE,

    CONSTRAINT ck_portfolio_asset_purchases_quantity_positive
        CHECK (quantity > 0),

    CONSTRAINT ck_portfolio_asset_purchases_price_non_negative
        CHECK (purchase_price >= 0)
);

CREATE INDEX idx_portfolio_asset_purchases_user_asset
    ON portfolio_asset_purchases(user_id, asset_id);

INSERT INTO portfolio_asset_purchases (user_id, asset_id, quantity, purchase_price, purchase_date)
SELECT user_id, asset_id, quantity, 0, NOW()
FROM portfolio_holdings
WHERE quantity > 0;

ALTER TABLE portfolio_holdings
    DROP COLUMN quantity;

COMMIT;
