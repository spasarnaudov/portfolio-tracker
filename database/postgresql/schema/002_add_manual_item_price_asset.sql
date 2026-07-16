-- Link jewelry/manual items to an automatically imported asset price series.
-- A NULL value keeps the existing fixed-price behavior.
ALTER TABLE portfolio_manual_items
    ADD COLUMN IF NOT EXISTS price_asset_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_portfolio_manual_items_price_asset'
            AND conrelid = 'portfolio_manual_items'::regclass
    ) THEN
        ALTER TABLE portfolio_manual_items
            ADD CONSTRAINT fk_portfolio_manual_items_price_asset
            FOREIGN KEY (price_asset_id)
            REFERENCES assets(id)
            ON DELETE SET NULL;
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_portfolio_manual_items_price_asset_id
    ON portfolio_manual_items(price_asset_id);
