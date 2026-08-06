-- One-off, hand-run migration for existing databases created before purchase
-- lots could have a receipt photo attached. Run once via psql, the same way
-- as 001_add_portfolio_asset_purchases.sql (see docs/database-operations.md).
-- Fresh installs never need this — schema/001_init_schema.sql already
-- reflects the target shape.

BEGIN;

ALTER TABLE portfolio_asset_purchases
    ADD COLUMN receipt_filename VARCHAR(255);

COMMIT;
