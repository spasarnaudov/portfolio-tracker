CREATE TABLE IF NOT EXISTS portfolio_manual_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    quantity NUMERIC(18, 6) NOT NULL DEFAULT 0,
    unit_price NUMERIC(18, 6) NOT NULL DEFAULT 0
);
