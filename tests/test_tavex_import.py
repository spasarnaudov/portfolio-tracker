import os
import sys
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASK_APP_DIRECTORY = PROJECT_ROOT / "apps" / "flask"
sys.path.insert(0, str(FLASK_APP_DIRECTORY))
os.environ.setdefault("APP_ENV", "test")

import tavex_import


class TavexImportTests(unittest.TestCase):
    def test_gold_buyback_prices_become_separate_chart_products(self):
        products = tavex_import.gold_buyback_prices_to_products([
            {
                "karat": 14,
                "fineness": 585,
                "price_per_gram": Decimal("52.25"),
            },
            {
                "karat": 18,
                "fineness": 750,
                "price_per_gram": Decimal("67.00"),
            },
        ])

        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]["name"], "1 грам злато изкупува - 14K / проба 585")
        self.assertEqual(products[0]["category_name"], "Gold buyback")
        self.assertEqual(products[0]["buy_price_eur"], Decimal("52.25"))

    def test_hourly_import_stores_buyback_prices_with_other_products(self):
        product = {
            "name": "Tavex product",
            "category_name": "Gold",
            "buy_price_eur": Decimal("100"),
        }
        buyback_price = {
            "karat": 14,
            "fineness": 585,
            "price_per_gram": Decimal("52.25"),
        }
        price_time = datetime(2026, 7, 15, 8, 0)

        with patch.object(
            tavex_import,
            "fetch_products_from_urls",
            return_value=([product], ["products-source"]),
        ), patch.object(
            tavex_import,
            "get_tavex_gold_buyback_prices",
            return_value=[buyback_price],
        ), patch.object(
            tavex_import,
            "import_assets_from_products",
            return_value={"imported_count": 1, "skipped_count": 1},
        ) as import_assets, patch.object(
            tavex_import,
            "import_asset_prices_by_name",
            return_value={"imported_count": 2, "missing_products": []},
        ) as import_prices:
            result = tavex_import.import_tavex_prices(price_time=price_time)

        imported_products = import_assets.call_args.args[0]
        self.assertEqual(len(imported_products), 2)
        self.assertEqual(imported_products[1]["category_name"], "Gold buyback")
        import_prices.assert_called_once_with(imported_products, price_time)
        self.assertEqual(result["buyback_products_count"], 1)
        self.assertIn(tavex_import.TAVEX_BUYBACK_URL, result["sources"])


if __name__ == "__main__":
    unittest.main()
