import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from automation import is_auto_tavex_import_enabled, set_auto_tavex_import_enabled
from chart_settings import load_chart_filters, save_chart_filters
from repository import (
    create_user,
    get_asset_by_id,
    get_asset_prices,
    get_assets,
    get_categories,
    get_chart_assets,
    get_dashboard_summary,
    get_latest_price_date,
    get_prices,
    get_portfolio_cash_items,
    get_portfolio_cash_total,
    get_portfolio_history,
    get_portfolio_holdings,
    get_portfolio_manual_items,
    get_portfolio_manual_total,
    get_user_by_id,
    get_user_by_username,
    get_user_with_password_by_id,
    get_users,
    save_portfolio_cash_items,
    save_portfolio_holdings,
    save_portfolio_manual_items,
    update_user_active_status,
    update_user_password,
    update_user_role,
)
from tavex_import import (
    current_timestamp,
    get_tavex_gold_buyback_prices,
    import_tavex_prices as run_tavex_import,
)

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "dev-secret-change-me")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TAVEX_IMPORT_LOG_PATH = PROJECT_ROOT / "logs" / "tavex_import.log"
DEFAULT_CHART_RANGE = "1d"
DEFAULT_CHART_INTERVAL = "recorded"
VALID_CHART_RANGES = {"1d", "1w", "1m", "ytd", "1y", "all", "custom"}
VALID_CHART_INTERVALS = {"recorded", "hourly", "daily", "weekly", "monthly"}
VALID_PORTFOLIO_RANGES = {"1d", "1w", "1m", "ytd", "1y", "all"}
VALID_PORTFOLIO_INTERVALS = {"hourly", "daily", "weekly"}
PUBLIC_ENDPOINTS = {"login", "register", "static"}
ADMIN_ENDPOINTS = {
    "home",
    "toggle_auto_tavex_import",
    "categories",
    "assets",
    "prices",
    "import_tavex_prices",
}
USER_MANAGEMENT_ENDPOINTS = {"users", "save_users"}
ROLE_MANAGER_ENDPOINTS = USER_MANAGEMENT_ENDPOINTS | {"change_password", "logout", "static"}
VALID_USER_ROLES = {"admin", "user", "demo"}
ROLE_MANAGER_USERNAME = "admin"


def is_admin(user):
    return user and user["role"] == "admin"


def is_role_manager(user):
    return is_admin(user) and user["username"].lower() == ROLE_MANAGER_USERNAME


def is_demo_user(user):
    return user and user["role"] == "demo"


def is_safe_next_url(next_url):
    if not next_url:
        return False

    parsed_url = urlsplit(next_url)
    return not parsed_url.netloc and parsed_url.path.startswith("/")


def add_query_parameter(next_url, name, value):
    parsed_url = urlsplit(next_url)
    query_items = [
        (query_name, query_value)
        for query_name, query_value in parse_qsl(parsed_url.query, keep_blank_values=True)
        if query_name != name
    ]
    query_items.append((name, value))

    return urlunsplit((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        urlencode(query_items),
        parsed_url.fragment,
    ))


@app.before_request
def require_login():
    g.current_user = None

    if request.endpoint in PUBLIC_ENDPOINTS:
        return None

    if request.endpoint is None:
        return None

    user_id = session.get("user_id")

    if user_id:
        user = get_user_by_id(user_id)

        if user and user["is_active"]:
            g.current_user = user

            if is_role_manager(user) and request.endpoint not in ROLE_MANAGER_ENDPOINTS:
                return redirect(url_for("users"))

            if is_demo_user(user) and request.endpoint == "change_password":
                return redirect(url_for("portfolio"))

            if request.endpoint in USER_MANAGEMENT_ENDPOINTS and not is_role_manager(user):
                if is_admin(user):
                    return redirect(url_for("home"))

                return redirect(url_for("portfolio"))

            if request.endpoint in ADMIN_ENDPOINTS and not is_admin(user):
                return redirect(url_for("portfolio"))

            return None

        session.clear()

    return redirect(url_for("login", next=request.full_path))


@app.context_processor
def inject_current_user():
    return {"current_user": getattr(g, "current_user", None)}


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


def get_holding_chart_payload(asset_id, selected_range, selected_interval):
    latest_price_date = get_latest_price_date(asset_id)
    start_date, end_date = get_chart_date_range(
        selected_range,
        latest_price_date,
        None,
        None,
    )
    prices = get_asset_prices(
        asset_id,
        start_date,
        end_date,
        selected_interval,
    )

    return {
        "labels": [
            format_chart_label(price["price_date"], selected_interval)
            for price in prices
        ],
        "values": [
            float(price["price"])
            for price in prices
        ],
        "interval": selected_interval,
        "has_prices": bool(prices),
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("home"))

    error = None
    next_url = request.args.get("next") or request.form.get("next") or url_for("home")

    if not is_safe_next_url(next_url):
        next_url = url_for("home")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_username(username) if username else None

        if user and user["is_active"] and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(next_url)

        error = "Invalid username or password."

    return render_template("login.html", error=error, next_url=next_url)


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("home"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            user = create_user(username, generate_password_hash(password), "user")

            if user:
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]

                return redirect(url_for("home"))

            error = "This username is already taken."

    return render_template("register.html", error=error)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    error = None
    next_url = request.form.get("next_url") or request.referrer or url_for("home")

    if not is_safe_next_url(next_url):
        next_url = url_for("home")

    if request.method == "GET":
        return redirect(next_url)

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")
    user = get_user_with_password_by_id(session["user_id"])

    if not user or not check_password_hash(user["password_hash"], current_password):
        error = "Current password is not correct."
    elif len(new_password) < 4:
        error = "New password must be at least 4 characters."
    elif new_password != confirm_password:
        error = "New passwords do not match."
    else:
        update_user_password(session["user_id"], generate_password_hash(new_password))
        flash("Password changed successfully.", "password_success")
        return redirect(add_query_parameter(next_url, "password_dialog", "1"))

    flash(error, "password_error")
    return redirect(add_query_parameter(next_url, "password_dialog", "1"))


@app.route("/users")
def users():
    return render_template(
        "users.html",
        users=get_users(),
        roles=[
            ("admin", "admin"),
            ("user", "user"),
            ("demo", "demo"),
        ],
    )


@app.route("/users/save", methods=["POST"])
def save_users():
    user_ids = request.form.getlist("user_id")
    active_user_ids = set(request.form.getlist("is_active"))

    for raw_user_id in user_ids:
        try:
            user_id = int(raw_user_id)
        except ValueError:
            continue

        if user_id == session["user_id"]:
            continue

        role = request.form.get(f"role_{user_id}", "")

        if role in VALID_USER_ROLES:
            update_user_role(user_id, role)

        update_user_active_status(user_id, str(user_id) in active_user_ids)

    return redirect(url_for("users"))


@app.route("/")
def home():
    if not is_admin(g.current_user):
        return redirect(url_for("portfolio"))

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
    user_id = session["user_id"]

    if request.method == "POST":
        quantities_by_asset_id = {}
        manual_items = []
        cash_items = []
        manual_item_ids = request.form.getlist("manual_item_id")
        manual_item_names = request.form.getlist("manual_item_name")
        manual_item_quantities = request.form.getlist("manual_item_quantity")
        manual_item_unit_prices = request.form.getlist("manual_item_unit_price")
        deleted_manual_item_ids = set(request.form.getlist("manual_item_delete"))
        cash_item_ids = request.form.getlist("cash_item_id")
        cash_item_names = request.form.getlist("cash_item_name")
        cash_item_amounts = request.form.getlist("cash_item_amount")
        deleted_cash_item_ids = set(request.form.getlist("cash_item_delete"))

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

        for index, raw_item_id in enumerate(cash_item_ids):
            try:
                item_id = int(raw_item_id)
                amount = float(cash_item_amounts[index] or 0)
            except (IndexError, ValueError):
                continue

            cash_items.append({
                "id": item_id,
                "name": cash_item_names[index] if index < len(cash_item_names) else "",
                "amount": amount,
                "delete": raw_item_id in deleted_cash_item_ids,
            })

        new_cash_item_name = request.form.get("new_cash_item_name", "").strip()

        if new_cash_item_name:
            try:
                new_cash_item_amount = float(request.form.get("new_cash_item_amount") or 0)
            except ValueError:
                new_cash_item_amount = 0

            cash_items.append({
                "id": None,
                "name": new_cash_item_name,
                "amount": new_cash_item_amount,
                "delete": False,
            })

        save_portfolio_holdings(user_id, quantities_by_asset_id)
        save_portfolio_manual_items(user_id, manual_items)
        save_portfolio_cash_items(user_id, cash_items)
        return redirect(url_for("portfolio"))

    holdings = get_portfolio_holdings(user_id)
    manual_items = get_portfolio_manual_items(user_id)
    cash_items = get_portfolio_cash_items(user_id)
    dashboard = get_dashboard_summary()
    portfolio_range = request.args.get("portfolio_range", DEFAULT_CHART_RANGE)
    portfolio_interval = request.args.get("portfolio_interval", "hourly")

    if portfolio_range not in VALID_PORTFOLIO_RANGES:
        portfolio_range = DEFAULT_CHART_RANGE

    if portfolio_interval not in VALID_PORTFOLIO_INTERVALS:
        portfolio_interval = "hourly"

    expanded_holding_id = request.args.get("expanded_holding_id", type=int)
    requested_holding_asset_id = request.args.get("holding_asset_id", type=int)
    requested_holding_range = request.args.get("holding_range", portfolio_range)
    requested_holding_interval = request.args.get("holding_interval", portfolio_interval)
    holding_filter_mode = request.args.get("holding_filter_mode", "custom")

    if holding_filter_mode not in {"main", "custom"}:
        holding_filter_mode = "custom"

    if requested_holding_range not in VALID_PORTFOLIO_RANGES:
        requested_holding_range = portfolio_range

    if requested_holding_interval not in VALID_PORTFOLIO_INTERVALS:
        requested_holding_interval = portfolio_interval

    portfolio_start_date, portfolio_end_date = get_chart_date_range(
        portfolio_range,
        dashboard["latest_price_date"],
        None,
        None,
    )
    portfolio_history = get_portfolio_history(
        user_id,
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
    manual_total = float(get_portfolio_manual_total(user_id) or 0)
    cash_total = float(get_portfolio_cash_total(user_id) or 0)
    total_value = tavex_total + manual_total + cash_total

    chart_labels = [
        format_chart_label(price["price_date"], portfolio_interval)
        for price in portfolio_history
    ]
    chart_values = [
        float(price["value"])
        for price in portfolio_history
    ]
    holding_charts = {}

    for holding in holdings:
        holding_range = portfolio_range
        holding_interval = portfolio_interval

        if holding_filter_mode == "custom" and holding["asset_id"] == requested_holding_asset_id:
            holding_range = requested_holding_range
            holding_interval = requested_holding_interval

        holding_chart = get_holding_chart_payload(
            holding["asset_id"],
            holding_range,
            holding_interval,
        )
        holding_charts[holding["asset_id"]] = {
            "range": holding_range,
            "interval": holding_interval,
            "labels": holding_chart["labels"],
            "values": holding_chart["values"],
            "has_prices": holding_chart["has_prices"],
        }

    return render_template(
        "portfolio.html",
        holdings=holdings,
        holding_charts=holding_charts,
        expanded_holding_id=expanded_holding_id,
        holding_filter_mode=holding_filter_mode,
        manual_items=manual_items,
        cash_items=cash_items,
        tavex_total=tavex_total,
        manual_total=manual_total,
        cash_total=cash_total,
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


@app.route("/api/portfolio/holding-chart")
def portfolio_holding_chart_api():
    asset_id = request.args.get("asset_id", type=int)
    selected_range = request.args.get("range", DEFAULT_CHART_RANGE)
    selected_interval = request.args.get("interval", "hourly")

    if not asset_id or not get_asset_by_id(asset_id):
        return jsonify({"error": "Unknown asset."}), 404

    if selected_range not in VALID_PORTFOLIO_RANGES:
        return jsonify({"error": "Unknown chart range."}), 400

    if selected_interval not in VALID_PORTFOLIO_INTERVALS:
        return jsonify({"error": "Unknown chart interval."}), 400

    return jsonify(get_holding_chart_payload(
        asset_id,
        selected_range,
        selected_interval,
    ))


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
    chart_user_id = None if is_admin(g.current_user) else session["user_id"]
    assets = get_chart_assets(chart_user_id)
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
