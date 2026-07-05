from flask import Flask, render_template, request
from psycopg.rows import dict_row

from db import get_connection

app = Flask(__name__)


@app.route("/")
def home():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM asset_categories) AS category_count,
                    (SELECT COUNT(*) FROM assets) AS asset_count,
                    (SELECT COUNT(*) FROM asset_prices) AS price_count,
                    (SELECT MAX(price_date) FROM asset_prices) AS latest_price_date;
            """)
            dashboard = cur.fetchone()

    return render_template("index.html", dashboard=dashboard)


@app.route("/categories")
def categories():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, name
                FROM asset_categories
                ORDER BY id;
            """)
            categories = cur.fetchall()

    return render_template("categories.html", categories=categories)


@app.route("/assets")
def assets():
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
            assets = cur.fetchall()

    return render_template("assets.html", assets=assets)


@app.route("/prices")
def prices():
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
            prices = cur.fetchall()

    return render_template("prices.html", prices=prices)


@app.route("/charts")
def charts():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, symbol, name
                FROM assets
                ORDER BY assets.symbol;
            """)
            assets = cur.fetchall()

            selected_asset_id = request.args.get("asset_id", type=int)

            if not selected_asset_id and assets:
                selected_asset_id = assets[0]["id"]

            start_date = request.args.get("start_date") or None
            end_date = request.args.get("end_date") or None
            selected_asset = None
            prices = []

            if selected_asset_id:
                cur.execute("""
                    SELECT id, symbol, name
                    FROM assets
                    WHERE id = %s;
                """, (selected_asset_id,))
                selected_asset = cur.fetchone()

                cur.execute("""
                    SELECT price_date, price
                    FROM asset_prices
                    WHERE asset_id = %s
                        AND (%s::date IS NULL OR price_date >= %s::date)
                        AND (%s::date IS NULL OR price_date <= %s::date)
                    ORDER BY price_date;
                """, (
                    selected_asset_id,
                    start_date,
                    start_date,
                    end_date,
                    end_date,
                ))
                prices = cur.fetchall()

    chart_labels = [
        price["price_date"].isoformat()
        for price in prices
    ]
    chart_values = [
        float(price["price"])
        for price in prices
    ]

    return render_template(
        "charts.html",
        assets=assets,
        selected_asset=selected_asset,
        selected_asset_id=selected_asset_id,
        start_date=start_date,
        end_date=end_date,
        prices=prices,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
