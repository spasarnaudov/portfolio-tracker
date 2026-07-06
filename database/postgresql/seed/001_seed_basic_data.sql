INSERT INTO asset_categories (name)
VALUES
    ('Stocks'),
    ('ETFs'),
    ('Crypto'),
    ('Cash'),
    ('Gold')
ON CONFLICT (name) DO NOTHING;

INSERT INTO assets (symbol, name, category_id)
VALUES
    ('AAPL', 'Apple Inc.', 1),
    ('MSFT', 'Microsoft Corporation', 1),
    ('VWCE', 'Vanguard FTSE All-World UCITS ETF', 2),
    ('BTC', 'Bitcoin', 3),
    ('ETH', 'Ethereum', 3)
ON CONFLICT (symbol) DO NOTHING;

WITH price_config AS (
    SELECT *
    FROM (
        VALUES
            ('AAPL', 205.00, 2.80),
            ('MSFT', 440.00, 5.60),
            ('VWCE', 120.00, 1.30),
            ('BTC', 62000.00, 2400.00),
            ('ETH', 3500.00, 160.00)
    ) AS config(symbol, base_price, wave_size)
),
generated_days AS (
    SELECT
        generated_date::date AS price_date,
        generated_date::date - DATE '2024-07-11' AS day_index
    FROM generate_series(
        DATE '2024-07-11',
        DATE '2026-07-11',
        INTERVAL '1 day'
    ) AS generated_date
),
market_cycle AS (
    SELECT
        price_date,
        day_index,
        CASE
            WHEN day_index <= 60 THEN
                1.00 + (day_index / 60.0) * 0.10
            WHEN day_index <= 130 THEN
                1.10 - ((day_index - 60) / 70.0) * 0.22
            WHEN day_index <= 210 THEN
                0.88 + ((day_index - 130) / 80.0) * 0.24
            WHEN day_index <= 285 THEN
                1.12 - ((day_index - 210) / 75.0) * 0.18
            WHEN day_index <= 365 THEN
                0.94 + ((day_index - 285) / 80.0) * 0.30
            WHEN day_index <= 440 THEN
                1.24 - ((day_index - 365) / 75.0) * 0.26
            WHEN day_index <= 525 THEN
                0.98 + ((day_index - 440) / 85.0) * 0.20
            WHEN day_index <= 600 THEN
                1.18 - ((day_index - 525) / 75.0) * 0.30
            WHEN day_index <= 675 THEN
                0.88 + ((day_index - 600) / 75.0) * 0.28
            ELSE
                1.16 - ((day_index - 675) / 55.0) * 0.18
        END AS cycle_multiplier
    FROM generated_days
)
INSERT INTO asset_prices (asset_id, price_date, price)
SELECT
    assets.id,
    market_cycle.price_date,
    ROUND((
        price_config.base_price * market_cycle.cycle_multiplier
        + price_config.wave_size * SIN(
            market_cycle.day_index * 0.37 + assets.id
        )
        + price_config.wave_size * 0.45 * COS(
            market_cycle.day_index * 0.11 + assets.id * 2
        )
        + price_config.wave_size * 0.25 * SIN(
            market_cycle.day_index * 1.73 + assets.id * 3
        )
    )::numeric, 2) AS price
FROM assets
JOIN price_config
    ON assets.symbol = price_config.symbol
CROSS JOIN market_cycle
ON CONFLICT (asset_id, price_date)
DO UPDATE SET price = EXCLUDED.price;
