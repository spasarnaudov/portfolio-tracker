from psycopg.rows import dict_row

from config import ROLE_MANAGER_USERNAME
from db import get_connection


def get_user_by_id(user_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    id,
                    username,
                    role,
                    is_active,
                    active_session_token,
                    active_session_expires_at
                FROM users
                WHERE id = %s;
            """, (user_id,))
            return cur.fetchone()


def get_user_with_password_by_id(user_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    id,
                    username,
                    password_hash,
                    role,
                    is_active,
                    active_session_token,
                    active_session_expires_at
                FROM users
                WHERE id = %s;
            """, (user_id,))
            return cur.fetchone()


def get_user_by_username(username):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    id,
                    username,
                    password_hash,
                    role,
                    is_active,
                    active_session_token,
                    active_session_expires_at
                FROM users
                WHERE LOWER(username) = LOWER(%s);
            """, (username,))
            return cur.fetchone()


def save_user(username, password_hash, role="user"):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (username)
                DO UPDATE SET
                    password_hash = EXCLUDED.password_hash,
                    role = EXCLUDED.role,
                    is_active = TRUE
                RETURNING id, username, role;
            """, (username, password_hash, role))
            user = cur.fetchone()

        conn.commit()

    return user


def create_user(username, password_hash, role="user"):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                RETURNING id, username, role;
            """, (username, password_hash, role))
            user = cur.fetchone()

        conn.commit()

    return user


def update_user_password(user_id, password_hash):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET password_hash = %s
                WHERE id = %s;
            """, (password_hash, user_id))

        conn.commit()


def update_user_session(user_id, session_token, expires_at):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET
                    active_session_token = %s,
                    active_session_expires_at = %s
                WHERE id = %s;
            """, (session_token, expires_at, user_id))

        conn.commit()


def clear_user_session(user_id, session_token=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if session_token:
                cur.execute("""
                    UPDATE users
                    SET
                        active_session_token = NULL,
                        active_session_expires_at = NULL
                    WHERE id = %s
                        AND active_session_token = %s;
                """, (user_id, session_token))
            else:
                cur.execute("""
                    UPDATE users
                    SET
                        active_session_token = NULL,
                        active_session_expires_at = NULL
                    WHERE id = %s;
                """, (user_id,))

        conn.commit()


def get_users():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, username, role, is_active, created_at
                FROM users
                ORDER BY LOWER(username);
            """)
            return cur.fetchall()


def update_user_role(user_id, role):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                UPDATE users
                SET role = %s
                WHERE id = %s
                    AND LOWER(username) != LOWER(%s)
                RETURNING id, username, role;
            """, (role, user_id, ROLE_MANAGER_USERNAME))
            user = cur.fetchone()

        conn.commit()

    return user


def update_user_active_status(user_id, is_active):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                UPDATE users
                SET is_active = %s
                WHERE id = %s
                    AND LOWER(username) != LOWER(%s)
                RETURNING id, username, is_active;
            """, (is_active, user_id, ROLE_MANAGER_USERNAME))
            user = cur.fetchone()

        conn.commit()

    return user


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


def get_portfolio_holdings(user_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    assets.id AS asset_id,
                    assets.symbol,
                    assets.name,
                    COALESCE(portfolio_holdings.quantity, 0) AS quantity,
                    COALESCE(portfolio_holdings.include_in_chart, FALSE) AS include_in_chart,
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
                    AND portfolio_holdings.user_id = %s
                LEFT JOIN LATERAL (
                    SELECT price_date, price
                    FROM asset_prices
                    WHERE asset_prices.asset_id = assets.id
                    ORDER BY price_date DESC
                    LIMIT 1
                ) AS latest_prices ON TRUE
                WHERE assets.symbol LIKE 'TAVEX-%%'
                ORDER BY assets.symbol, assets.name;
            """, (user_id,))
            return cur.fetchall()


def save_portfolio_holdings(user_id, quantities_by_asset_id, chart_asset_ids):
    with get_connection() as conn:
        with conn.cursor() as cur:
            for asset_id, quantity in quantities_by_asset_id.items():
                include_in_chart = asset_id in chart_asset_ids

                if quantity <= 0:
                    cur.execute("""
                        DELETE FROM portfolio_holdings
                        WHERE user_id = %s
                            AND asset_id = %s;
                    """, (user_id, asset_id))
                    continue

                cur.execute("""
                    INSERT INTO portfolio_holdings (user_id, asset_id, quantity, include_in_chart)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id, asset_id)
                    DO UPDATE SET
                        quantity = EXCLUDED.quantity,
                        include_in_chart = EXCLUDED.include_in_chart;
                """, (user_id, asset_id, quantity, include_in_chart))

        conn.commit()


def get_portfolio_manual_items(user_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    id,
                    name,
                    quantity,
                    unit_price,
                    include_in_chart,
                    ROUND(quantity * unit_price, 2) AS current_value
                FROM portfolio_manual_items
                WHERE user_id = %s
                ORDER BY id;
            """, (user_id,))
            return cur.fetchall()


def save_portfolio_manual_items(user_id, items):
    with get_connection() as conn:
        with conn.cursor() as cur:
            for item in items:
                item_id = item.get("id")
                name = item.get("name", "").strip()
                quantity = item.get("quantity", 0)
                unit_price = item.get("unit_price", 0)
                include_in_chart = (
                    item.get("include_in_chart", False)
                    and quantity > 0
                )
                should_delete = item.get("delete", False)

                if item_id and (should_delete or not name):
                    cur.execute("""
                        DELETE FROM portfolio_manual_items
                        WHERE id = %s
                            AND user_id = %s;
                    """, (item_id, user_id))
                    continue

                if item_id:
                    cur.execute("""
                        UPDATE portfolio_manual_items
                        SET name = %s,
                            quantity = %s,
                            unit_price = %s,
                            include_in_chart = %s
                        WHERE id = %s
                            AND user_id = %s;
                    """, (name, quantity, unit_price, include_in_chart, item_id, user_id))
                    continue

                if name:
                    cur.execute("""
                        INSERT INTO portfolio_manual_items (
                            user_id, name, quantity, unit_price, include_in_chart
                        )
                        VALUES (%s, %s, %s, %s, %s);
                    """, (user_id, name, quantity, unit_price, include_in_chart))

        conn.commit()


def snapshot_portfolio_manual_item_prices(price_date):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO portfolio_manual_item_prices (
                    manual_item_id,
                    price_date,
                    price
                )
                SELECT id, %s, unit_price
                FROM portfolio_manual_items
                ON CONFLICT (manual_item_id, price_date)
                DO UPDATE SET price = EXCLUDED.price;
            """, (price_date,))
            imported_count = cur.rowcount

        conn.commit()

    return imported_count


def get_portfolio_history(user_id, start_date=None, end_date=None, interval="hourly"):
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
                WITH asset_period_prices AS (
                    SELECT
                        {group_expression} AS price_date,
                        asset_prices.asset_id,
                        portfolio_holdings.quantity,
                        AVG(asset_prices.price) AS price
                    FROM portfolio_holdings
                    JOIN asset_prices
                        ON asset_prices.asset_id = portfolio_holdings.asset_id
                    WHERE portfolio_holdings.quantity > 0
                        AND portfolio_holdings.user_id = %s
                        AND portfolio_holdings.include_in_chart = TRUE
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
                manual_period_prices AS (
                    SELECT
                        {group_expression} AS price_date,
                        portfolio_manual_items.id AS manual_item_id,
                        portfolio_manual_items.quantity,
                        AVG(portfolio_manual_item_prices.price) AS price
                    FROM portfolio_manual_items
                    JOIN portfolio_manual_item_prices
                        ON portfolio_manual_item_prices.manual_item_id = portfolio_manual_items.id
                    WHERE portfolio_manual_items.quantity > 0
                        AND portfolio_manual_items.user_id = %s
                        AND portfolio_manual_items.include_in_chart = TRUE
                        AND (%s::timestamp IS NULL OR portfolio_manual_item_prices.price_date >= %s::timestamp)
                        AND (%s::timestamp IS NULL OR portfolio_manual_item_prices.price_date <= %s::timestamp)
                    GROUP BY
                        {group_expression},
                        portfolio_manual_items.id,
                        portfolio_manual_items.quantity
                ),
                manual_history AS (
                    SELECT
                        price_date,
                        SUM(quantity * price) AS value
                    FROM manual_period_prices
                    GROUP BY price_date
                ),
                portfolio_dates AS (
                    SELECT price_date
                    FROM tavex_history
                    UNION
                    SELECT price_date
                    FROM manual_history
                )
                SELECT
                    portfolio_dates.price_date,
                    ROUND(
                        COALESCE(tavex_history.value, 0)
                        + COALESCE(manual_history.value, 0),
                        2
                    ) AS value
                FROM portfolio_dates
                LEFT JOIN tavex_history
                    ON tavex_history.price_date = portfolio_dates.price_date
                LEFT JOIN manual_history
                    ON manual_history.price_date = portfolio_dates.price_date
                ORDER BY portfolio_dates.price_date;
            """.format(group_expression=group_expression), (
                user_id,
                start_date,
                start_date,
                end_date,
                end_date,
                user_id,
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
