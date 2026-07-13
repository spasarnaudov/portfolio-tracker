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

    def test_successful_login_is_recorded(self):
        connection, cursor = self._connection_and_cursor()

        with patch.object(repository, "get_connection", return_value=connection):
            repository.record_user_login(7)

        query, parameters = cursor.execute.call_args.args
        self.assertIn("INSERT INTO user_login_history", query)
        self.assertEqual(parameters, (7,))
        connection.commit.assert_called_once_with()

    def test_login_history_is_ordered_from_newest_to_oldest(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchall.return_value = []

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_user_login_history()

        query = cursor.execute.call_args.args[0]
        self.assertIn("user_login_history.username", query)
        self.assertNotIn("JOIN users", query)
        self.assertIn("logged_in_at DESC", query)

    def test_login_user_filter_includes_current_and_historical_users(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchall.return_value = [
            {"username": "admin"},
            {"username": "deleted_user"},
        ]

        with patch.object(repository, "get_connection", return_value=connection):
            usernames = repository.get_user_login_users()

        query = cursor.execute.call_args.args[0]
        self.assertIn("FROM users", query)
        self.assertIn("FROM user_login_history", query)
        self.assertEqual(usernames, ["admin", "deleted_user"])

    def test_account_soft_deletion_protects_role_manager_and_preserves_user(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchone.return_value = {"id": 7}

        with patch.object(repository, "get_connection", return_value=connection):
            deactivated = repository.deactivate_user_account(7)

        query, parameters = cursor.execute.call_args.args
        self.assertTrue(deactivated)
        self.assertIn("UPDATE users", query)
        self.assertIn("is_deleted = TRUE", query)
        self.assertIn("LOWER(username) != LOWER(%s)", query)
        self.assertEqual(parameters, (7, repository.ROLE_MANAGER_USERNAME))
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
