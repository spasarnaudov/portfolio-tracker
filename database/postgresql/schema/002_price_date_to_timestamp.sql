ALTER TABLE asset_prices
    ALTER COLUMN price_date TYPE TIMESTAMP
    USING price_date::timestamp;
