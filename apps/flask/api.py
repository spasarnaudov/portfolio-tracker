import math
import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps

from flask import Blueprint, Response, current_app, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from chart_settings import load_chart_filters, save_chart_filters
from config import PROJECT_ROOT, ROLE_MANAGER_USERNAME, SESSION_TIMEOUT_MINUTES
from log_reader import get_log_files
from repository import (
    clear_user_session,
    create_user,
    deactivate_user_account,
    get_asset_prices,
    get_chart_assets,
    get_gold_buyback_assets,
    get_latest_price_date,
    get_portfolio_history,
    get_portfolio_holdings,
    get_portfolio_manual_items,
    get_user_by_session_token,
    get_user_by_username,
    get_users,
    get_user_login_history,
    record_user_login,
    save_portfolio_holdings,
    save_portfolio_manual_items,
    update_user_password,
    update_user_session,
)

api = Blueprint("api", __name__, url_prefix="/api/v1")
SESSION_TIMEOUT = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
CHART_RANGES = {"1d", "1w", "1m", "ytd", "1y", "all", "custom"}
CHART_INTERVALS = {"recorded", "hourly", "daily", "weekly", "monthly"}
PORTFOLIO_RANGES = {"1d", "1w", "1m", "ytd", "1y", "all"}
PORTFOLIO_INTERVALS = {"hourly", "daily", "weekly"}


def _serialize(value):
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _response(data, status=200):
    return jsonify(_serialize(data)), status


def _error(code, message, status, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return _response(body, status)


def _json_body():
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else None


def _public_user(user):
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


def _issue_token(user):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + SESSION_TIMEOUT
    update_user_session(user["id"], token, expires_at)
    record_user_login(user["id"])
    return token, expires_at


def require_api_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            return _error("authentication_required", "A Bearer token is required.", 401)
        user = get_user_by_session_token(token)
        now = datetime.now()
        if (
            not user
            or user["is_deleted"]
            or not secrets.compare_digest(user["active_session_token"] or "", token)
            or not user["active_session_expires_at"]
            or user["active_session_expires_at"] <= now
        ):
            return _error("invalid_token", "The token is invalid or expired.", 401)
        update_user_session(user["id"], token, now + SESSION_TIMEOUT)
        g.api_user = user
        g.api_token = token
        if user["role"] == "admin" and user["username"].lower() == ROLE_MANAGER_USERNAME:
            allowed = {"api.logout", "api.session_status", "api.change_password"}
            if request.endpoint not in allowed and not request.endpoint.startswith("api.admin_"):
                return _error("forbidden", "The role-manager account cannot access portfolio data.", 403)
        return view(*args, **kwargs)
    return wrapped


def require_admin(view):
    @wraps(view)
    @require_api_auth
    def wrapped(*args, **kwargs):
        if g.api_user["role"] != "admin":
            return _error("forbidden", "Administrator access is required.", 403)
        return view(*args, **kwargs)
    return wrapped


def _date_range(selected_range, latest_date, start_date=None, end_date=None):
    if selected_range == "custom":
        return start_date, end_date
    if selected_range == "all":
        return None, None
    end_date = latest_date
    if selected_range == "1d" and latest_date:
        start_date = latest_date - timedelta(days=1)
    elif selected_range == "1w" and latest_date:
        start_date = latest_date - timedelta(days=7)
    elif selected_range == "1m" and latest_date:
        start_date = latest_date - timedelta(days=30)
    elif selected_range == "ytd" and latest_date:
        start_date = latest_date.replace(month=1, day=1)
    elif selected_range == "1y" and latest_date:
        start_date = latest_date - timedelta(days=365)
    return start_date, end_date


def _iso_date(value, field):
    if value in (None, ""):
        return None, None
    try:
        return date.fromisoformat(value).isoformat(), None
    except (TypeError, ValueError):
        return None, f"{field} must use YYYY-MM-DD format."


@api.get("/health")
def health():
    return _response({"status": "ok", "api_version": "v1"})


@api.post("/auth/login")
def login():
    body = _json_body()
    if body is None:
        return _error("invalid_json", "A JSON object is required.", 400)
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))
    user = get_user_by_username(username) if username else None
    if not user or user["is_deleted"] or not check_password_hash(user["password_hash"], password):
        return _error("invalid_credentials", "Invalid username or password.", 401)
    active = user["active_session_token"] and user["active_session_expires_at"] and user["active_session_expires_at"] > datetime.now()
    if active and body.get("force") is not True:
        return _error("active_session", "This account already has an active session.", 409)
    if active:
        clear_user_session(user["id"])
    token, expires_at = _issue_token(user)
    return _response({"token": token, "token_type": "Bearer", "expires_at": expires_at, "user": _public_user(user)})


@api.post("/auth/register")
def register():
    body = _json_body()
    if body is None:
        return _error("invalid_json", "A JSON object is required.", 400)
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))
    if len(username) < 3:
        return _error("invalid_username", "Username must be at least 3 characters.", 422)
    if len(password) < 8:
        return _error("invalid_password", "Password must be at least 8 characters.", 422)
    user = create_user(username, generate_password_hash(password))
    if not user:
        return _error("username_taken", "This username is already taken.", 409)
    token, expires_at = _issue_token(user)
    return _response({"token": token, "token_type": "Bearer", "expires_at": expires_at, "user": _public_user(user)}, 201)


@api.post("/auth/logout")
@require_api_auth
def logout():
    clear_user_session(g.api_user["id"], g.api_token)
    return "", 204


@api.get("/auth/session")
@require_api_auth
def session_status():
    return _response({"authenticated": True, "user": _public_user(g.api_user)})


@api.put("/account/password")
@require_api_auth
def change_password():
    body = _json_body()
    if body is None:
        return _error("invalid_json", "A JSON object is required.", 400)
    user = get_user_by_username(g.api_user["username"])
    current_password = str(body.get("current_password", ""))
    new_password = str(body.get("new_password", ""))
    if not user or not check_password_hash(user["password_hash"], current_password):
        return _error("invalid_password", "Current password is not correct.", 422)
    if len(new_password) < 8:
        return _error("invalid_new_password", "New password must be at least 8 characters.", 422)
    update_user_password(user["id"], generate_password_hash(new_password))
    return _response({"message": "Password changed successfully."})


@api.delete("/account")
@require_api_auth
def delete_account():
    if not deactivate_user_account(g.api_user["id"]):
        return _error("account_not_deactivated", "This account cannot be deactivated.", 409)
    return "", 204


@api.get("/assets")
@require_api_auth
def assets():
    return _response({"assets": get_chart_assets(), "gold_buyback_assets": get_gold_buyback_assets()})


@api.get("/assets/<int:asset_id>/prices")
@require_api_auth
def asset_prices(asset_id):
    if asset_id not in {asset["id"] for asset in get_chart_assets()}:
        return _error("asset_not_found", "Asset not found.", 404)
    selected_range = request.args.get("range", "1d")
    interval = request.args.get("interval", "recorded")
    if selected_range not in CHART_RANGES:
        return _error("invalid_range", "Unsupported chart range.", 422)
    if interval not in CHART_INTERVALS:
        return _error("invalid_interval", "Unsupported chart interval.", 422)
    start_date, start_error = _iso_date(request.args.get("start_date"), "start_date")
    end_date, end_error = _iso_date(request.args.get("end_date"), "end_date")
    if start_error or end_error:
        return _error("invalid_date", start_error or end_error, 422)
    if selected_range == "custom" and (not start_date or not end_date):
        return _error("invalid_date", "start_date and end_date are required for a custom range.", 422)
    if start_date and end_date and start_date > end_date:
        start_date, end_date = end_date, start_date
    start_date, end_date = _date_range(selected_range, get_latest_price_date(asset_id), start_date, end_date)
    return _response({
        "asset_id": asset_id, "range": selected_range, "interval": interval,
        "start_date": start_date, "end_date": end_date,
        "prices": get_asset_prices(asset_id, start_date, end_date, interval),
    })


@api.get("/portfolio")
@require_api_auth
def portfolio():
    user_id = g.api_user["id"]
    holdings = get_portfolio_holdings(user_id)
    manual_items = get_portfolio_manual_items(user_id)
    total_value = sum(
        (item.get("current_value") or 0 for item in [*holdings, *manual_items]),
        Decimal("0"),
    )
    return _response({
        "holdings": holdings,
        "manual_items": manual_items,
        "total_value": total_value,
        "gold_buyback_assets": get_gold_buyback_assets(),
    })


@api.put("/portfolio")
@require_api_auth
def update_portfolio():
    body = _json_body()
    if body is None:
        return _error("invalid_json", "A JSON object is required.", 400)
    holdings = body.get("holdings", [])
    manual_items = body.get("manual_items", [])
    if not isinstance(holdings, list) or not isinstance(manual_items, list):
        return _error("invalid_portfolio", "holdings and manual_items must be arrays.", 422)
    valid_holding_ids = {item["asset_id"] for item in get_portfolio_holdings(g.api_user["id"])}
    valid_price_ids = {item["id"] for item in get_gold_buyback_assets()}
    quantities, chart_ids, normalized, errors = {}, set(), [], []
    for index, holding in enumerate(holdings):
        try:
            asset_id = int(holding["asset_id"])
            quantity = float(holding.get("quantity", 0))
        except (KeyError, TypeError, ValueError):
            errors.append(f"holdings[{index}] is invalid.")
            continue
        if asset_id not in valid_holding_ids or not math.isfinite(quantity) or quantity < 0:
            errors.append(f"holdings[{index}] has an invalid asset or quantity.")
            continue
        quantities[asset_id] = quantity
        if quantity > 0 and holding.get("include_in_chart") is True:
            chart_ids.add(asset_id)
    for index, item in enumerate(manual_items):
        try:
            item_id = int(item["id"]) if item.get("id") is not None else None
            name = str(item.get("name", "")).strip()
            quantity = float(item.get("quantity", 0))
            unit_price = float(item.get("unit_price") or 0)
            price_asset_id = int(item["price_asset_id"]) if item.get("price_asset_id") is not None else None
        except (AttributeError, TypeError, ValueError):
            errors.append(f"manual_items[{index}] is invalid.")
            continue
        if not math.isfinite(quantity) or not math.isfinite(unit_price) or quantity < 0 or unit_price < 0:
            errors.append(f"manual_items[{index}] contains an invalid number.")
            continue
        if price_asset_id is not None and price_asset_id not in valid_price_ids:
            errors.append(f"manual_items[{index}].price_asset_id is invalid.")
            continue
        normalized.append({
            "id": item_id, "name": name, "quantity": quantity, "unit_price": unit_price,
            "price_asset_id": price_asset_id,
            "include_in_chart": item.get("include_in_chart") is True and quantity > 0,
            "delete": item.get("delete") is True,
        })
    if errors:
        return _error("validation_failed", "The portfolio payload is invalid.", 422, errors)
    save_portfolio_holdings(g.api_user["id"], quantities, chart_ids)
    save_portfolio_manual_items(g.api_user["id"], normalized)
    return portfolio()


@api.get("/portfolio/history")
@require_api_auth
def portfolio_history():
    selected_range = request.args.get("range", "1d")
    interval = request.args.get("interval", "hourly")
    if selected_range not in PORTFOLIO_RANGES:
        return _error("invalid_range", "Unsupported portfolio range.", 422)
    if interval not in PORTFOLIO_INTERVALS:
        return _error("invalid_interval", "Unsupported portfolio interval.", 422)
    start_date, end_date = _date_range(selected_range, get_latest_price_date())
    return _response({
        "range": selected_range, "interval": interval, "start_date": start_date,
        "end_date": end_date,
        "points": get_portfolio_history(g.api_user["id"], start_date, end_date, interval),
    })


@api.get("/charts/configuration")
@require_api_auth
def chart_configuration():
    return _response(load_chart_filters())


@api.put("/charts/configuration")
@require_api_auth
def update_chart_configuration():
    body = _json_body()
    if body is None or not isinstance(body.get("charts"), list):
        return _error("invalid_configuration", "charts must be an array.", 422)
    save_chart_filters(body)
    return _response(body)


@api.get("/admin/users")
@require_admin
def admin_users():
    return _response(get_users())


@api.get("/admin/login-stats")
@require_admin
def admin_login_stats():
    users = get_users()
    return _response({user["username"]: user["login_count"] for user in users})


@api.get("/admin/login-history")
@require_admin
def admin_login_history():
    return _response(get_user_login_history())


@api.get("/admin/logs")
@require_admin
def admin_logs():
    return _response(get_log_files(PROJECT_ROOT / "logs"))


@api.get("/admin/logs/<path:name>")
@require_admin
def admin_log_content(name):
    log_file = next(
        (item for item in get_log_files(PROJECT_ROOT / "logs") if item["name"] == name),
        None,
    )
    if not log_file:
        return _error("log_not_found", "Log file not found.", 404)
    return Response(log_file["content"], mimetype="text/plain")


@api.errorhandler(Exception)
def api_internal_error(error):
    current_app.logger.exception("Unhandled API error", exc_info=error)
    return _error("internal_error", "An unexpected server error occurred.", 500)
