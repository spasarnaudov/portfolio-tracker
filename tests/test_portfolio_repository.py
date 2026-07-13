import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASK_APP_DIRECTORY = PROJECT_ROOT / "apps" / "flask"
sys.path.insert(0, str(FLASK_APP_DIRECTORY))
os.environ.setdefault("APP_ENV", "test")

import repository


class PortfolioRepositoryTests(unittest.TestCase):
    def _connection_and_cursor(self):
        connection = MagicMock()
        connection.__enter__.return_value = connection
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        return connection, cursor

    def test_manual_item_price_snapshot_uses_one_price_per_item_and_hour(self):
        connection, cursor = self._connection_and_cursor()
        cursor.rowcount = 3
        price_date = datetime(2026, 7, 14, 9, 0)

        with patch.object(repository, "get_connection", return_value=connection):
            imported_count = repository.snapshot_portfolio_manual_item_prices(price_date)

        self.assertEqual(imported_count, 3)
        query, parameters = cursor.execute.call_args.args
        self.assertIn("ON CONFLICT (manual_item_id, price_date)", query)
        self.assertEqual(parameters, (price_date,))
        connection.commit.assert_called_once_with()

    def test_portfolio_history_uses_recorded_manual_item_prices(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchall.return_value = []

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_portfolio_history(7, interval="hourly")

        query = cursor.execute.call_args.args[0]
        self.assertIn("JOIN portfolio_manual_item_prices", query)
        self.assertIn("manual_history", query)
        self.assertNotIn("manual_total", query)


if __name__ == "__main__":
    unittest.main()
