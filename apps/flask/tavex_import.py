import sys
from datetime import datetime
from pathlib import Path

from repository import import_assets_from_products, import_asset_prices_by_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_PATH = PROJECT_ROOT / "scripts"

if str(SCRIPTS_PATH) not in sys.path:
    sys.path.append(str(SCRIPTS_PATH))

from fetch_tavex_prices import DEFAULT_CATEGORY_URLS, fetch_products_from_urls


def current_timestamp():
    return datetime.now().replace(microsecond=0)


def current_hour_timestamp():
    return datetime.now().replace(minute=0, second=0, microsecond=0)


def import_tavex_prices(price_time=None, timeout=15):
    products, sources = fetch_products_from_urls(DEFAULT_CATEGORY_URLS, timeout=timeout)
    assets_result = import_assets_from_products(products)
    prices_result = import_asset_prices_by_name(
        products,
        price_time or current_timestamp(),
    )

    return {
        "sources": sources,
        "products_count": len(products),
        "imported_assets_count": assets_result["imported_count"],
        "skipped_assets_count": assets_result["skipped_count"],
        "imported_prices_count": prices_result["imported_count"],
        "missing_products": prices_result["missing_products"],
    }
