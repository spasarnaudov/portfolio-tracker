from datetime import timedelta
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

from automation import is_auto_tavex_import_enabled, set_auto_tavex_import_enabled
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
from tavex_import import current_timestamp, import_tavex_prices as run_tavex_import

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TAVEX_IMPORT_LOG_PATH = PROJECT_ROOT / "logs" / "tavex_import.log"


def format_date_value(value):
    if not value:
        return ""

    if hasattr(value, "date"):
        return value.date().isoformat()

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def format_chart_label(value, interval):
    if not value:
        return ""

    if interval == "recorded" and hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    if interval == "hourly" and hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")

    if hasattr(value, "date"):
        return value.date().isoformat()

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def get_last_query_value(name, default=None):
    values = request.args.getlist(name)

    if not values:
        return default

    return values[-1]


def get_tavex_import_log_lines(limit=12):
    if not TAVEX_IMPORT_LOG_PATH.exists():
        return []

    return TAVEX_IMPORT_LOG_PATH.read_text().splitlines()[-limit:]


@app.route("/")
def home():
    dashboard = get_dashboard_summary()
    return render_template(
        "index.html",
        dashboard=dashboard,
        auto_tavex_import_enabled=is_auto_tavex_import_enabled(),
        tavex_import_log_lines=get_tavex_import_log_lines(),
    )


@app.route("/automation/tavex-import", methods=["POST"])
def toggle_auto_tavex_import():
    enabled = request.form.get("enabled") == "true"
    set_auto_tavex_import_enabled(enabled)

    return redirect(url_for("home"))


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
    return render_template(
        "prices.html",
        prices=prices,
        imported_count=request.args.get("imported", type=int),
        missing_count=request.args.get("missing", type=int),
        imported_assets_count=request.args.get("imported_assets", type=int),
        skipped_assets_count=request.args.get("skipped_assets", type=int),
    )


@app.route("/prices/import-tavex", methods=["POST"])
def import_tavex_prices():
    result = run_tavex_import(price_time=current_timestamp())

    return redirect(url_for(
        "prices",
        imported=result["imported_prices_count"],
        missing=len(result["missing_products"]),
        imported_assets=result["imported_assets_count"],
        skipped_assets=result["skipped_assets_count"],
    ))


@app.route("/charts")
def charts():
    assets = get_chart_assets()
    selected_asset_id = request.args.get("asset_id", type=int)
    selected_range = get_last_query_value("range", "1d")
    selected_interval = get_last_query_value("interval", "recorded")

    if not selected_asset_id and assets:
        selected_asset_id = assets[0]["id"]

    if selected_range not in {"1d", "1w", "1m", "ytd", "1y", "all", "custom"}:
        selected_range = "1d"

    if selected_interval not in {"recorded", "hourly", "daily", "weekly", "monthly"}:
        selected_interval = "recorded"

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

            if selected_range == "1d" and latest_price_date:
                start_date = latest_price_date - timedelta(days=1)
            elif selected_range == "1w" and latest_price_date:
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
        format_chart_label(price["price_date"], selected_interval)
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
