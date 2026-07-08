from datetime import timedelta
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

from automation import is_auto_tavex_import_enabled, set_auto_tavex_import_enabled
from chart_settings import load_chart_filters, save_chart_filters
from repository import (
    get_asset_by_id,
    get_asset_prices,
    get_assets,
    get_categories,
    get_chart_assets,
    get_dashboard_summary,
    get_latest_price_date,
    get_prices,
    get_portfolio_history,
    get_portfolio_holdings,
    get_portfolio_manual_items,
    get_portfolio_manual_total,
    save_portfolio_holdings,
    save_portfolio_manual_items,
)
from tavex_import import (
    current_timestamp,
    get_tavex_gold_buyback_prices,
    import_tavex_prices as run_tavex_import,
)

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TAVEX_IMPORT_LOG_PATH = PROJECT_ROOT / "logs" / "tavex_import.log"
DEFAULT_CHART_RANGE = "1d"
DEFAULT_CHART_INTERVAL = "recorded"
VALID_CHART_RANGES = {"1d", "1w", "1m", "ytd", "1y", "all", "custom"}
VALID_CHART_INTERVALS = {"recorded", "hourly", "daily", "weekly", "monthly"}
VALID_PORTFOLIO_RANGES = {"1d", "1w", "1m", "ytd", "1y", "all"}
VALID_PORTFOLIO_INTERVALS = {"hourly", "daily", "weekly"}


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


def get_chart_list_value(values, index, default=None):
    if index >= len(values):
        return default

    value = values[index]

    if value in {None, ""}:
        return default

    return value


def normalize_chart_config(chart_config, valid_asset_ids):
    try:
        asset_id = int(chart_config.get("asset_id"))
    except (TypeError, ValueError):
        return None

    if asset_id not in valid_asset_ids:
        return None

    selected_range = chart_config.get("range") or DEFAULT_CHART_RANGE
    selected_interval = chart_config.get("interval") or DEFAULT_CHART_INTERVAL

    if selected_range not in VALID_CHART_RANGES:
        selected_range = DEFAULT_CHART_RANGE

    if selected_interval not in VALID_CHART_INTERVALS:
        selected_interval = DEFAULT_CHART_INTERVAL

    return {
        "asset_id": asset_id,
        "range": selected_range,
        "interval": selected_interval,
        "start_date": chart_config.get("start_date") or None,
        "end_date": chart_config.get("end_date") or None,
    }


def get_requested_chart_configs(saved_filters, valid_asset_ids):
    chart_configs = []
    selected_asset_ids = set()

    if request.args:
        raw_asset_ids = request.args.getlist("chart_asset_id")
        ranges = request.args.getlist("chart_range")
        intervals = request.args.getlist("chart_interval")
        start_dates = request.args.getlist("chart_start_date")
        end_dates = request.args.getlist("chart_end_date")

        for index, raw_asset_id in enumerate(raw_asset_ids):
            chart_config = normalize_chart_config({
                "asset_id": raw_asset_id,
                "range": get_chart_list_value(ranges, index, DEFAULT_CHART_RANGE),
                "interval": get_chart_list_value(intervals, index, DEFAULT_CHART_INTERVAL),
                "start_date": get_chart_list_value(start_dates, index),
                "end_date": get_chart_list_value(end_dates, index),
            }, valid_asset_ids)

            if not chart_config or chart_config["asset_id"] in selected_asset_ids:
                continue

            chart_configs.append(chart_config)
            selected_asset_ids.add(chart_config["asset_id"])
    else:
        saved_charts = saved_filters.get("charts", [])

        for saved_chart in saved_charts:
            chart_config = normalize_chart_config(saved_chart, valid_asset_ids)

            if not chart_config or chart_config["asset_id"] in selected_asset_ids:
                continue

            chart_configs.append(chart_config)
            selected_asset_ids.add(chart_config["asset_id"])

    remove_chart_index = request.args.get("remove_chart", type=int)

    if remove_chart_index is not None and 0 <= remove_chart_index < len(chart_configs):
        removed_chart = chart_configs.pop(remove_chart_index)
        selected_asset_ids.discard(removed_chart["asset_id"])

    if "add_chart" in request.args:
        for asset_id in valid_asset_ids:
            if asset_id not in selected_asset_ids:
                chart_configs.append({
                    "asset_id": asset_id,
                    "range": DEFAULT_CHART_RANGE,
                    "interval": DEFAULT_CHART_INTERVAL,
                    "start_date": None,
                    "end_date": None,
                })
                break

    return chart_configs


def get_chart_date_range(selected_range, latest_price_date, custom_start_date, custom_end_date):
    start_date = custom_start_date
    end_date = custom_end_date

    if selected_range == "custom":
        return start_date, end_date

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

    return start_date, end_date


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


@app.route("/portfolio", methods=["GET", "POST"])
def portfolio():
    if request.method == "POST":
        quantities_by_asset_id = {}
        manual_items = []
        manual_item_ids = request.form.getlist("manual_item_id")
        manual_item_names = request.form.getlist("manual_item_name")
        manual_item_quantities = request.form.getlist("manual_item_quantity")
        manual_item_unit_prices = request.form.getlist("manual_item_unit_price")
        deleted_manual_item_ids = set(request.form.getlist("manual_item_delete"))

        for key, value in request.form.items():
            if not key.startswith("quantity_"):
                continue

            try:
                asset_id = int(key.replace("quantity_", "", 1))
                quantity = float(value or 0)
            except ValueError:
                continue

            quantities_by_asset_id[asset_id] = quantity

        for index, raw_item_id in enumerate(manual_item_ids):
            try:
                item_id = int(raw_item_id)
                quantity = float(manual_item_quantities[index] or 0)
                unit_price = float(manual_item_unit_prices[index] or 0)
            except (IndexError, ValueError):
                continue

            manual_items.append({
                "id": item_id,
                "name": manual_item_names[index] if index < len(manual_item_names) else "",
                "quantity": quantity,
                "unit_price": unit_price,
                "delete": raw_item_id in deleted_manual_item_ids,
            })

        new_manual_item_name = request.form.get("new_manual_item_name", "").strip()

        if new_manual_item_name:
            try:
                new_manual_item_quantity = float(request.form.get("new_manual_item_quantity") or 0)
                new_manual_item_unit_price = float(request.form.get("new_manual_item_unit_price") or 0)
            except ValueError:
                new_manual_item_quantity = 0
                new_manual_item_unit_price = 0

            manual_items.append({
                "id": None,
                "name": new_manual_item_name,
                "quantity": new_manual_item_quantity,
                "unit_price": new_manual_item_unit_price,
                "delete": False,
            })

        save_portfolio_holdings(quantities_by_asset_id)
        save_portfolio_manual_items(manual_items)
        return redirect(url_for("portfolio"))

    holdings = get_portfolio_holdings()
    manual_items = get_portfolio_manual_items()
    dashboard = get_dashboard_summary()
    portfolio_range = request.args.get("portfolio_range", DEFAULT_CHART_RANGE)
    portfolio_interval = request.args.get("portfolio_interval", "hourly")

    if portfolio_range not in VALID_PORTFOLIO_RANGES:
        portfolio_range = DEFAULT_CHART_RANGE

    if portfolio_interval not in VALID_PORTFOLIO_INTERVALS:
        portfolio_interval = "hourly"

    portfolio_start_date, portfolio_end_date = get_chart_date_range(
        portfolio_range,
        dashboard["latest_price_date"],
        None,
        None,
    )
    portfolio_history = get_portfolio_history(
        portfolio_start_date,
        portfolio_end_date,
        portfolio_interval,
    )
    tavex_gold_price_per_gram = None
    tavex_gold_buyback_prices = []

    try:
        tavex_gold_buyback_prices = get_tavex_gold_buyback_prices()
        tavex_gold_price_per_gram = next(
            (
                price
                for price in tavex_gold_buyback_prices
                if price["karat"] == 14
            ),
            tavex_gold_buyback_prices[0] if tavex_gold_buyback_prices else None,
        )
    except Exception:
        tavex_gold_buyback_prices = []
        tavex_gold_price_per_gram = None

    tavex_total = sum(
        float(holding["current_value"] or 0)
        for holding in holdings
    )
    manual_total = float(get_portfolio_manual_total() or 0)
    total_value = tavex_total + manual_total

    chart_labels = [
        format_chart_label(price["price_date"], portfolio_interval)
        for price in portfolio_history
    ]
    chart_values = [
        float(price["value"])
        for price in portfolio_history
    ]

    return render_template(
        "portfolio.html",
        holdings=holdings,
        manual_items=manual_items,
        tavex_total=tavex_total,
        manual_total=manual_total,
        total_value=total_value,
        tavex_gold_price_per_gram=tavex_gold_price_per_gram,
        tavex_gold_buyback_prices=tavex_gold_buyback_prices,
        portfolio_range=portfolio_range,
        portfolio_interval=portfolio_interval,
        portfolio_ranges=[
            ("1d", "1 Day"),
            ("1w", "1 Week"),
            ("1m", "1 Month"),
            ("ytd", "YTD"),
            ("1y", "1 Year"),
            ("all", "All"),
        ],
        portfolio_intervals=[
            ("hourly", "Hourly"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
        ],
        chart_labels=chart_labels,
        chart_values=chart_values,
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
    saved_filters = load_chart_filters()
    asset_ids = [asset["id"] for asset in assets]
    assets_by_id = {
        asset["id"]: asset
        for asset in assets
    }
    chart_configs = get_requested_chart_configs(saved_filters, asset_ids)
    selected_asset_ids = [
        chart_config["asset_id"]
        for chart_config in chart_configs
    ]
    selected_asset_id_set = set(selected_asset_ids)
    chart_panels = []

    for index, chart_config in enumerate(chart_configs):
        asset_id = chart_config["asset_id"]
        selected_asset = assets_by_id.get(asset_id) or get_asset_by_id(asset_id)
        latest_price_date = get_latest_price_date(asset_id)
        start_date, end_date = get_chart_date_range(
            chart_config["range"],
            latest_price_date,
            chart_config["start_date"],
            chart_config["end_date"],
        )
        prices = get_asset_prices(
            asset_id,
            start_date,
            end_date,
            chart_config["interval"],
        )
        selectable_assets = [
            asset
            for asset in assets
            if asset["id"] == asset_id or asset["id"] not in selected_asset_id_set
        ]

        chart_panels.append({
            "index": index,
            "asset": selected_asset,
            "asset_id": asset_id,
            "selectable_assets": selectable_assets,
            "range": chart_config["range"],
            "interval": chart_config["interval"],
            "start_date": chart_config["start_date"] or "",
            "end_date": chart_config["end_date"] or "",
            "labels": [
                format_chart_label(price["price_date"], chart_config["interval"])
                for price in prices
            ],
            "values": [
                float(price["price"])
                for price in prices
            ],
            "has_prices": bool(prices),
        })

    save_chart_filters({
        "charts": chart_configs,
        "asset_ids": selected_asset_ids,
        "range": DEFAULT_CHART_RANGE,
        "interval": DEFAULT_CHART_INTERVAL,
        "start_date": None,
        "end_date": None,
    })
    can_add_chart = len(selected_asset_ids) < len(assets)

    return render_template(
        "charts.html",
        assets=assets,
        chart_panels=chart_panels,
        can_add_chart=can_add_chart,
        chart_ranges=[
            ("1d", "1 Day"),
            ("1w", "1 Week"),
            ("1m", "1 Month"),
            ("ytd", "YTD"),
            ("1y", "1 Year"),
            ("all", "All"),
            ("custom", "Custom"),
        ],
        chart_intervals=[
            ("recorded", "Each record"),
            ("hourly", "Hourly Avg"),
            ("daily", "Daily Avg"),
            ("weekly", "Weekly Avg"),
            ("monthly", "Monthly Avg"),
        ],
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
