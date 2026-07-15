#!/usr/bin/env python3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASK_APP_PATH = PROJECT_ROOT / "apps" / "flask"

if str(FLASK_APP_PATH) not in sys.path:
    sys.path.append(str(FLASK_APP_PATH))

from automation import is_auto_tavex_import_enabled
from repository import snapshot_portfolio_manual_item_prices
from tavex_import import current_hour_timestamp, import_tavex_prices


def main():
    price_time = current_hour_timestamp()
    manual_prices_count = snapshot_portfolio_manual_item_prices(price_time)

    print(f"Hourly price time: {price_time}")
    print(f"Stored manual item prices: {manual_prices_count}")

    if not is_auto_tavex_import_enabled():
        print("Automatic Tavex import is disabled.")
        return

    result = import_tavex_prices(price_time=price_time)

    print(f"Fetched products: {result['products_count']}")
    print(f"Gold buyback price series: {result['buyback_products_count']}")
    print(f"Imported missing assets: {result['imported_assets_count']}")
    print(f"Skipped existing assets: {result['skipped_assets_count']}")
    print(f"Imported prices: {result['imported_prices_count']}")
    print(f"Missing products: {len(result['missing_products'])}")


if __name__ == "__main__":
    main()
