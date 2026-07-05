from flask import Flask, render_template, request

from repository import (
    get_asset_by_id,
    get_asset_prices,
    get_assets,
    get_categories,
    get_chart_assets,
    get_dashboard_summary,
    get_prices,
)

app = Flask(__name__)


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

    if not selected_asset_id and assets:
        selected_asset_id = assets[0]["id"]

    start_date = request.args.get("start_date") or None
    end_date = request.args.get("end_date") or None
    selected_asset = None
    prices = []

    if selected_asset_id:
        selected_asset = get_asset_by_id(selected_asset_id)
        prices = get_asset_prices(selected_asset_id, start_date, end_date)

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
