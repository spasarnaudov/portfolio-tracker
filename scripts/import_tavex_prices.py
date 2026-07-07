#!/usr/bin/env python3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASK_APP_PATH = PROJECT_ROOT / "apps" / "flask"

if str(FLASK_APP_PATH) not in sys.path:
    sys.path.append(str(FLASK_APP_PATH))

from automation import is_auto_tavex_import_enabled
from tavex_import import current_hour_timestamp, import_tavex_prices


def main():
    if not is_auto_tavex_import_enabled():
        print("Automatic Tavex import is disabled.")
        return

    price_time = current_hour_timestamp()
    result = import_tavex_prices(price_time=price_time)

    print(f"Tavex import time: {price_time}")
    print(f"Fetched products: {result['products_count']}")
    print(f"Imported missing assets: {result['imported_assets_count']}")
    print(f"Skipped existing assets: {result['skipped_assets_count']}")
    print(f"Imported prices: {result['imported_prices_count']}")
    print(f"Missing products: {len(result['missing_products'])}")


if __name__ == "__main__":
    main()
