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
                    (SELECT MAX(price_date) FROM asset_prices) AS latest_price_date;
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


def get_asset_prices(asset_id, start_date=None, end_date=None):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT price_date, price
                FROM asset_prices
                WHERE asset_id = %s
                    AND (%s::date IS NULL OR price_date >= %s::date)
                    AND (%s::date IS NULL OR price_date <= %s::date)
                ORDER BY price_date;
            """, (
                asset_id,
                start_date,
                start_date,
                end_date,
                end_date,
            ))
            return cur.fetchall()
