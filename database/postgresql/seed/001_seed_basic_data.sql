INSERT INTO asset_categories (name)
VALUES
    ('Stocks'),
    ('ETFs'),
    ('Crypto'),
    ('Cash'),
    ('Gold');

INSERT INTO assets (symbol, name, category_id)
VALUES
    ('AAPL', 'Apple Inc.', 1),
    ('MSFT', 'Microsoft Corporation', 1),
    ('VWCE', 'Vanguard FTSE All-World UCITS ETF', 2),
    ('BTC', 'Bitcoin', 3),
    ('ETH', 'Ethereum', 3);

INSERT INTO asset_prices (asset_id, price_date, price)
VALUES
    (1, '2026-06-28', 210.50),
    (1, '2026-06-29', 212.10),
    (1, '2026-06-30', 211.75),

    (2, '2026-06-28', 450.00),
    (2, '2026-06-29', 452.35),
    (2, '2026-06-30', 451.20),

    (3, '2026-06-28', 120.35),
    (3, '2026-06-29', 121.10),
    (3, '2026-06-30', 120.80),

    (4, '2026-06-28', 61000.00),
    (4, '2026-06-29', 62050.00),
    (4, '2026-06-30', 61800.00),

    (5, '2026-06-28', 3400.00),
    (5, '2026-06-29', 3450.00),
    (5, '2026-06-30', 3425.00);