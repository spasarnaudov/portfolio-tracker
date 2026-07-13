WITH demo_user AS (
    SELECT id
    FROM users
    WHERE LOWER(username) = LOWER('demo')
),
demo_assets AS (
    SELECT
        assets.id,
        ROW_NUMBER() OVER (ORDER BY assets.symbol) AS position
    FROM assets
    WHERE assets.symbol LIKE 'TAVEX-%'
    ORDER BY assets.symbol
    LIMIT 5
),
demo_holdings AS (
    SELECT
        demo_user.id AS user_id,
        demo_assets.id AS asset_id,
        CASE demo_assets.position
            WHEN 1 THEN 1.00
            WHEN 2 THEN 2.00
            WHEN 3 THEN 5.00
            WHEN 4 THEN 10.00
            ELSE 3.00
        END AS quantity
    FROM demo_user
    CROSS JOIN demo_assets
)
INSERT INTO portfolio_holdings (user_id, asset_id, quantity, include_in_chart)
SELECT user_id, asset_id, quantity, TRUE
FROM demo_holdings
ON CONFLICT (user_id, asset_id)
DO UPDATE SET
    quantity = EXCLUDED.quantity,
    include_in_chart = EXCLUDED.include_in_chart;

INSERT INTO portfolio_manual_items (user_id, name, quantity, unit_price, include_in_chart)
SELECT users.id, 'demo jewelry 14K', 12.50, 95.00, TRUE
FROM users
WHERE LOWER(users.username) = LOWER('demo')
    AND NOT EXISTS (
        SELECT 1
        FROM portfolio_manual_items
        WHERE portfolio_manual_items.user_id = users.id
            AND portfolio_manual_items.name = 'demo jewelry 14K'
    );

INSERT INTO portfolio_manual_item_prices (manual_item_id, price_date, price)
SELECT
    portfolio_manual_items.id,
    hourly_prices.price_date,
    portfolio_manual_items.unit_price
FROM portfolio_manual_items
CROSS JOIN (
    SELECT DISTINCT DATE_TRUNC('hour', asset_prices.price_date) AS price_date
    FROM asset_prices
) AS hourly_prices
JOIN users
    ON users.id = portfolio_manual_items.user_id
WHERE LOWER(users.username) = LOWER('demo')
    AND portfolio_manual_items.name = 'demo jewelry 14K'
ON CONFLICT (manual_item_id, price_date)
DO UPDATE SET price = EXCLUDED.price;
