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
INSERT INTO portfolio_holdings (user_id, asset_id, quantity)
SELECT user_id, asset_id, quantity
FROM demo_holdings
ON CONFLICT (user_id, asset_id)
DO UPDATE SET quantity = EXCLUDED.quantity;

INSERT INTO portfolio_manual_items (user_id, name, quantity, unit_price)
SELECT users.id, 'demo jewelry 14K', 12.50, 95.00
FROM users
WHERE LOWER(users.username) = LOWER('demo')
    AND NOT EXISTS (
        SELECT 1
        FROM portfolio_manual_items
        WHERE portfolio_manual_items.user_id = users.id
            AND portfolio_manual_items.name = 'demo jewelry 14K'
    );

INSERT INTO portfolio_cash_items (user_id, name, amount)
SELECT users.id, 'demo bank savings', 1500.00
FROM users
WHERE LOWER(users.username) = LOWER('demo')
    AND NOT EXISTS (
        SELECT 1
        FROM portfolio_cash_items
        WHERE portfolio_cash_items.user_id = users.id
            AND portfolio_cash_items.name = 'demo bank savings'
    );
