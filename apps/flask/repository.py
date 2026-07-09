from psycopg.rows import dict_row

from db import get_connection


def get_dashboard_summary():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM asset_categories) AS category_count,
                    (SELECT COUNT(*) FROM assets) AS asset_count,
                    (SELECT COUNT(*) FROM asset_prices) AS price_count,
                    (SELECT MAX(price_date) FROM asset_prices) AS latest_price_date,
                    ROUND(pg_database_size(current_database()) / 1024.0 / 1024.0, 2) AS database_size_mb;
            """)
            return cur.fetchone()


def get_categories():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, name
                FROM asset_categories
                ORDER BY id;
            """)
            return cur.fetchall()


def get_assets():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    assets.id,
                    assets.symbol,
                    assets.name,
                    asset_categories.name AS category_name
                FROM assets
                JOIN asset_categories
                    ON assets.category_id = asset_categories.id
                ORDER BY assets.id;
            """)
            return cur.fetchall()


def get_prices():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    assets.symbol,
                    assets.name,
                    asset_prices.price_date,
                    asset_prices.price
                FROM asset_prices
                JOIN assets
                    ON asset_prices.asset_id = assets.id
                ORDER BY asset_prices.price_date DESC, assets.symbol;
            """)
            return cur.fetchall()


def get_portfolio_holdings():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    assets.id AS asset_id,
                    assets.symbol,
                    assets.name,
                    COALESCE(portfolio_holdings.quantity, 0) AS quantity,
                    latest_prices.price_date,
                    latest_prices.price,
                    ROUND(
                        COALESCE(portfolio_holdings.quantity, 0)
                        * COALESCE(latest_prices.price, 0),
                        2
                    ) AS current_value
                FROM assets
                LEFT JOIN portfolio_holdings
                    ON portfolio_holdings.asset_id = assets.id
                LEFT JOIN LATERAL (
                    SELECT price_date, price
                    FROM asset_prices
                    WHERE asset_prices.asset_id = assets.id
                    ORDER BY price_date DESC
                    LIMIT 1
                ) AS latest_prices ON TRUE
                WHERE assets.symbol LIKE 'TAVEX-%'
                ORDER BY assets.symbol, assets.name;
            """)
            return cur.fetchall()


def save_portfolio_holdings(quantities_by_asset_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            for asset_id, quantity in quantities_by_asset_id.items():
                if quantity <= 0:
                    cur.execute("""
                        DELETE FROM portfolio_holdings
                        WHERE asset_id = %s;
                    """, (asset_id,))
                    continue

                cur.execute("""
                    INSERT INTO portfolio_holdings (asset_id, quantity)
                    VALUES (%s, %s)
                    ON CONFLICT (asset_id)
                    DO UPDATE SET quantity = EXCLUDED.quantity;
                """, (asset_id, quantity))

        conn.commit()


def get_portfolio_manual_items():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    id,
                    name,
                    quantity,
                    unit_price,
                    ROUND(quantity * unit_price, 2) AS current_value
                FROM portfolio_manual_items
                ORDER BY id;
            """)
            return cur.fetchall()


def save_portfolio_manual_items(items):
    with get_connection() as conn:
        with conn.cursor() as cur:
            for item in items:
                item_id = item.get("id")
                name = item.get("name", "").strip()
                quantity = item.get("quantity", 0)
                unit_price = item.get("unit_price", 0)
                should_delete = item.get("delete", False)

                if item_id and (should_delete or not name):
                    cur.execute("""
                        DELETE FROM portfolio_manual_items
                        WHERE id = %s;
                    """, (item_id,))
                    continue

                if item_id:
                    cur.execute("""
                        UPDATE portfolio_manual_items
                        SET name = %s,
                            quantity = %s,
                            unit_price = %s
                        WHERE id = %s;
                    """, (name, quantity, unit_price, item_id))
                    continue

                if name:
                    cur.execute("""
                        INSERT INTO portfolio_manual_items (name, quantity, unit_price)
                        VALUES (%s, %s, %s);
                    """, (name, quantity, unit_price))

        conn.commit()


def get_portfolio_manual_total():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT ROUND(COALESCE(SUM(quantity * unit_price), 0), 2) AS total
                FROM portfolio_manual_items;
            """)
            return cur.fetchone()["total"]


def get_portfolio_cash_items():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, name, amount
                FROM portfolio_cash_items
                ORDER BY id;
            """)
            return cur.fetchall()


def save_portfolio_cash_items(items):
    with get_connection() as conn:
        with conn.cursor() as cur:
            for item in items:
                item_id = item.get("id")
                name = item.get("name", "").strip()
                amount = item.get("amount", 0)
                should_delete = item.get("delete", False)

                if item_id and (should_delete or not name):
                    cur.execute("""
                        DELETE FROM portfolio_cash_items
                        WHERE id = %s;
                    """, (item_id,))
                    continue

                if item_id:
                    cur.execute("""
                        UPDATE portfolio_cash_items
                        SET name = %s,
                            amount = %s
                        WHERE id = %s;
                    """, (name, amount, item_id))
                    continue

                if name:
                    cur.execute("""
                        INSERT INTO portfolio_cash_items (name, amount)
                        VALUES (%s, %s);
                    """, (name, amount))

        conn.commit()


def get_portfolio_cash_total():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT ROUND(COALESCE(SUM(amount), 0), 2) AS total
                FROM portfolio_cash_items;
            """)
            return cur.fetchone()["total"]


def get_portfolio_history(start_date=None, end_date=None, interval="hourly"):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if interval == "recorded":
                group_expression = "price_date"
            elif interval == "daily":
                group_expression = "DATE_TRUNC('day', price_date)::date"
            elif interval == "weekly":
                group_expression = "DATE_TRUNC('week', price_date)::date"
            else:
                group_expression = "DATE_TRUNC('hour', price_date)"

            cur.execute("""
                WITH manual_total AS (
                    SELECT COALESCE(SUM(quantity * unit_price), 0) AS value
                    FROM portfolio_manual_items
                ),
                cash_total AS (
                    SELECT COALESCE(SUM(amount), 0) AS value
                    FROM portfolio_cash_items
                ),
                static_total AS (
                    SELECT manual_total.value + cash_total.value AS value
                    FROM manual_total
                    CROSS JOIN cash_total
                ),
                asset_period_prices AS (
                    SELECT
                        {group_expression} AS price_date,
                        asset_prices.asset_id,
                        portfolio_holdings.quantity,
                        AVG(asset_prices.price) AS price
                    FROM portfolio_holdings
                    JOIN asset_prices
                        ON asset_prices.asset_id = portfolio_holdings.asset_id
                    WHERE portfolio_holdings.quantity > 0
                        AND (%s::timestamp IS NULL OR asset_prices.price_date >= %s::timestamp)
                        AND (%s::timestamp IS NULL OR asset_prices.price_date <= %s::timestamp)
                    GROUP BY {group_expression}, asset_prices.asset_id, portfolio_holdings.quantity
                ),
                tavex_history AS (
                    SELECT
                        price_date,
                        SUM(quantity * price) AS value
                    FROM asset_period_prices
                    GROUP BY price_date
                ),
                manual_only_history AS (
                    SELECT
                        {group_expression} AS price_date,
                        0 AS value
                    FROM asset_prices
                    WHERE (SELECT value FROM static_total) > 0
                        AND NOT EXISTS (SELECT 1 FROM tavex_history)
                        AND (%s::timestamp IS NULL OR asset_prices.price_date >= %s::timestamp)
                        AND (%s::timestamp IS NULL OR asset_prices.price_date <= %s::timestamp)
                    GROUP BY {group_expression}
                ),
                portfolio_history AS (
                    SELECT price_date, value
                    FROM tavex_history
                    UNION ALL
                    SELECT price_date, value
                    FROM manual_only_history
                )
                SELECT
                    portfolio_history.price_date,
                    ROUND(
                        portfolio_history.value
                        + static_total.value,
                        2
                    ) AS value
                FROM portfolio_history
                CROSS JOIN static_total
                ORDER BY portfolio_history.price_date;
            """.format(group_expression=group_expression), (
                start_date,
                start_date,
                end_date,
                end_date,
                start_date,
                start_date,
                end_date,
                end_date,
            ))
            return cur.fetchall()


def import_asset_prices_by_name(products, price_date):
    imported_count = 0
    missing_products = []

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for product in products:
                price = product.get("buy_price_eur")

                if not price:
                    missing_products.append(product["name"])
                    continue

                cur.execute("""
                    SELECT id
                    FROM assets
                    WHERE LOWER(name) = LOWER(%s);
                """, (product["name"],))
                asset = cur.fetchone()

                if not asset:
                    missing_products.append(product["name"])
                    continue

                cur.execute("""
                    INSERT INTO asset_prices (asset_id, price_date, price)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (asset_id, price_date)
                    DO UPDATE SET price = EXCLUDED.price;
                """, (
                    asset["id"],
                    price_date,
                    price,
                ))
                imported_count += 1

        conn.commit()

    return {
        "imported_count": imported_count,
        "missing_products": missing_products,
    }


def import_assets_from_products(products):
    imported_count = 0
    skipped_count = 0

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for product in products:
                cur.execute("""
                    SELECT id
                    FROM assets
                    WHERE LOWER(name) = LOWER(%s);
                """, (product["name"],))

                if cur.fetchone():
                    skipped_count += 1
                    continue

                category_name = product.get("category_name") or "Gold"

                cur.execute("""
                    INSERT INTO asset_categories (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id;
                """, (category_name,))
                category = cur.fetchone()

                cur.execute("""
                    SELECT COALESCE(MAX(id), 0) + 1 AS next_id
                    FROM assets;
                """)
                next_asset_id = cur.fetchone()["next_id"]
                symbol = f"TAVEX-{next_asset_id:03d}"

                cur.execute("""
                    INSERT INTO assets (symbol, name, category_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (symbol) DO NOTHING
                    RETURNING id;
                """, (
                    symbol,
                    product["name"],
                    category["id"],
                ))

                if cur.fetchone():
                    imported_count += 1

        conn.commit()

    return {
        "imported_count": imported_count,
        "skipped_count": skipped_count,
    }


def get_chart_assets():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, symbol, name
                FROM assets
                ORDER BY assets.symbol;
            """)
            return cur.fetchall()


def get_asset_by_id(asset_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, symbol, name
                FROM assets
                WHERE id = %s;
            """, (asset_id,))
            return cur.fetchone()


def get_latest_price_date(asset_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT MAX(price_date) AS latest_price_date
                FROM asset_prices
                WHERE asset_id = %s;
            """, (asset_id,))
            result = cur.fetchone()

            if not result:
                return None

            return result["latest_price_date"]


def get_asset_prices(asset_id, start_date=None, end_date=None, interval="daily"):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if interval == "recorded":
                group_expression = "price_date"
            elif interval == "hourly":
                group_expression = "DATE_TRUNC('hour', price_date)"
            elif interval == "weekly":
                group_expression = "DATE_TRUNC('week', price_date)::date"
            elif interval == "monthly":
                group_expression = "DATE_TRUNC('month', price_date)::date"
            else:
                group_expression = "DATE_TRUNC('day', price_date)::date"

            query = """
                SELECT
                    {group_expression} AS price_date,
                    ROUND(AVG(price), 2) AS price
                FROM asset_prices
                WHERE asset_id = %s
                    AND (%s::timestamp IS NULL OR price_date >= %s::timestamp)
                    AND (%s::date IS NULL OR price_date < (%s::date + INTERVAL '1 day'))
                GROUP BY {group_expression}
                ORDER BY {group_expression};
            """.format(group_expression=group_expression)

            cur.execute(query, (
                asset_id,
                start_date,
                start_date,
                end_date,
                end_date,
            ))
            return cur.fetchall()
