from datetime import timedelta

from flask import Flask, render_template, request

from repository import (
    get_asset_by_id,
    get_asset_prices,
    get_assets,
    get_categories,
    get_chart_assets,
    get_dashboard_summary,
    get_latest_price_date,
    get_prices,
)

app = Flask(__name__)


def format_date_value(value):
    if not value:
        return ""

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def get_last_query_value(name, default=None):
    values = request.args.getlist(name)

    if not values:
        return default

    return values[-1]


@app.route("/")
def home():
    dashboard = get_dashboard_summary()
    return render_template("index.html", dashboard=dashboard)


@app.route("/categories")
def categories():
    categories = get_categories()
    return render_template("categories.html", categories=categories)


@app.route("/assets")
def assets():
    assets = get_assets()
    return render_template("assets.html", assets=assets)


@app.route("/prices")
def prices():
    prices = get_prices()
    return render_template("prices.html", prices=prices)


@app.route("/charts")
def charts():
    assets = get_chart_assets()
    selected_asset_id = request.args.get("asset_id", type=int)
    selected_range = get_last_query_value("range", "1w")
    selected_interval = get_last_query_value("interval", "daily")

    if not selected_asset_id and assets:
        selected_asset_id = assets[0]["id"]

    if selected_range not in {"1w", "1m", "ytd", "1y", "all", "custom"}:
        selected_range = "1w"

    if selected_interval not in {"daily", "weekly", "monthly"}:
        selected_interval = "daily"

    custom_start_date = request.args.get("start_date") or None
    custom_end_date = request.args.get("end_date") or None
    start_date = custom_start_date
    end_date = custom_end_date
    selected_asset = None
    prices = []

    if selected_asset_id:
        selected_asset = get_asset_by_id(selected_asset_id)
        latest_price_date = get_latest_price_date(selected_asset_id)

        if selected_range != "custom":
            end_date = latest_price_date

            if selected_range == "1w" and latest_price_date:
                start_date = latest_price_date - timedelta(days=7)
            elif selected_range == "1m" and latest_price_date:
                start_date = latest_price_date - timedelta(days=30)
            elif selected_range == "ytd" and latest_price_date:
                start_date = latest_price_date.replace(month=1, day=1)
            elif selected_range == "1y" and latest_price_date:
                start_date = latest_price_date - timedelta(days=365)
            elif selected_range == "all":
                start_date = None
                end_date = None

        prices = get_asset_prices(
            selected_asset_id,
            start_date,
            end_date,
            selected_interval,
        )

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
        selected_range=selected_range,
        selected_interval=selected_interval,
        start_date=format_date_value(start_date),
        end_date=format_date_value(end_date),
        prices=prices,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
