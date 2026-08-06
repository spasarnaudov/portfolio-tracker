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
        self.assertIn("WHERE price_asset_id IS NULL", query)
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

    def test_portfolio_history_carries_last_known_prices_forward(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchall.return_value = []
        start_date = datetime(2026, 7, 14, 9, 0)
        end_date = datetime(2026, 7, 15, 9, 0)

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_portfolio_history(
                7,
                start_date=start_date,
                end_date=end_date,
                interval="hourly",
            )

        query, parameters = cursor.execute.call_args.args
        self.assertEqual(
            query.count("history.price_date <= portfolio_dates.price_date"),
            2,
        )
        self.assertEqual(query.count("ORDER BY history.price_date DESC"), 2)
        self.assertNotIn("COALESCE(tavex_history.value, 0)", query)
        self.assertNotIn("COALESCE(manual_history.value, 0)", query)
        self.assertEqual(parameters, (
            7,
            end_date,
            end_date,
            7,
            7,
            end_date,
            end_date,
            7,
            end_date,
            end_date,
            start_date,
            start_date,
            end_date,
            end_date,
        ))

    def test_all_database_assets_are_available_in_user_chart_products(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchall.return_value = []

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_chart_assets()

        query = cursor.execute.call_args.args[0]
        self.assertIn("FROM assets", query)
        self.assertNotIn("portfolio_holdings", query)
        self.assertNotIn("WHERE", query)

    def test_latest_price_date_supports_global_and_per_asset_queries(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchone.return_value = {"latest_price_date": datetime(2026, 7, 15, 8, 0)}

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_latest_price_date()

        global_query = cursor.execute.call_args.args[0]
        self.assertNotIn("WHERE asset_id", global_query)

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_latest_price_date(7)

        asset_query, parameters = cursor.execute.call_args.args
        self.assertIn("WHERE asset_id = %s", asset_query)
        self.assertEqual(parameters, (7,))

    def test_gold_buyback_assets_are_hidden_from_portfolio_holdings(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchall.return_value = []

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_portfolio_holdings(7)

        query, parameters = cursor.execute.call_args.args
        self.assertIn("asset_categories.name != 'Gold buyback'", query)
        self.assertIn("portfolio_asset_purchases", query)
        self.assertIn("profit", query)
        self.assertEqual(parameters, (7, 7))

    def test_holdings_quantity_and_cost_basis_come_from_purchase_lots(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchall.return_value = []

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_portfolio_holdings(7)

        query = cursor.execute.call_args.args[0]
        self.assertIn("SUM(quantity)", query)
        self.assertIn("SUM(quantity * purchase_price)", query)
        self.assertNotIn("portfolio_holdings.quantity", query)

    def test_save_holdings_chart_flags_updates_existing_rows_only(self):
        connection, cursor = self._connection_and_cursor()

        with patch.object(repository, "get_connection", return_value=connection):
            repository.save_holdings_chart_flags(7, {3, 5})

        query, parameters = cursor.execute.call_args.args
        self.assertIn("UPDATE portfolio_holdings", query)
        self.assertIn("asset_id = ANY(%s)", query)
        self.assertEqual(parameters, ([3, 5], 7))
        connection.commit.assert_called_once_with()

    def test_get_asset_purchases_orders_newest_first(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchall.return_value = []

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_asset_purchases(7, 3)

        query, parameters = cursor.execute.call_args.args
        self.assertIn("FROM portfolio_asset_purchases", query)
        self.assertIn("ORDER BY portfolio_asset_purchases.purchase_date DESC", query)
        self.assertEqual(parameters, (7, 3))

    def test_get_asset_purchases_computes_profit_from_the_latest_price(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchall.return_value = []

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_asset_purchases(7, 3)

        query = cursor.execute.call_args.args[0]
        self.assertIn("AS profit", query)
        self.assertIn("AS profit_percent", query)
        self.assertIn("FROM asset_prices", query)

    def test_add_asset_purchase_creates_the_holding_row(self):
        connection, cursor = self._connection_and_cursor()
        purchase_date = datetime(2026, 1, 5)
        cursor.fetchone.return_value = {
            "id": 1, "asset_id": 3, "quantity": 2.0,
            "purchase_price": 50.0, "purchase_date": purchase_date,
        }

        with patch.object(repository, "get_connection", return_value=connection):
            purchase = repository.add_asset_purchase(7, 3, 2.0, 50.0, purchase_date)

        self.assertEqual(purchase["id"], 1)
        insert_purchase_query = cursor.execute.call_args_list[0].args[0]
        insert_holding_query = cursor.execute.call_args_list[1].args[0]
        self.assertIn("INSERT INTO portfolio_asset_purchases", insert_purchase_query)
        self.assertIn("INSERT INTO portfolio_holdings", insert_holding_query)
        self.assertIn("ON CONFLICT (user_id, asset_id) DO NOTHING", insert_holding_query)
        connection.commit.assert_called_once_with()

    def test_update_asset_purchase_is_scoped_to_owner(self):
        connection, cursor = self._connection_and_cursor()
        purchase_date = datetime(2026, 1, 5)
        cursor.fetchone.return_value = {
            "id": 1, "asset_id": 3, "quantity": 4.0,
            "purchase_price": 55.0, "purchase_date": purchase_date,
        }

        with patch.object(repository, "get_connection", return_value=connection):
            purchase = repository.update_asset_purchase(7, 1, 4.0, 55.0, purchase_date)

        query, parameters = cursor.execute.call_args.args
        self.assertIn("UPDATE portfolio_asset_purchases", query)
        self.assertIn("WHERE id = %s", query)
        self.assertIn("AND user_id = %s", query)
        self.assertEqual(parameters, (4.0, 55.0, purchase_date, 1, 7))
        self.assertEqual(purchase["quantity"], 4.0)

    def test_delete_asset_purchase_removes_the_holding_when_it_was_the_last_lot(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchone.return_value = {"asset_id": 3}

        with patch.object(repository, "get_connection", return_value=connection):
            deleted = repository.delete_asset_purchase(7, 1)

        self.assertTrue(deleted)
        delete_purchase_query = cursor.execute.call_args_list[0].args[0]
        delete_holding_query, delete_holding_parameters = cursor.execute.call_args_list[1].args
        self.assertIn("DELETE FROM portfolio_asset_purchases", delete_purchase_query)
        self.assertIn("DELETE FROM portfolio_holdings", delete_holding_query)
        self.assertIn("NOT EXISTS", delete_holding_query)
        self.assertEqual(delete_holding_parameters, (7, 3, 7, 3))
        connection.commit.assert_called_once_with()

    def test_delete_asset_purchase_returns_false_when_not_found(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchone.return_value = None

        with patch.object(repository, "get_connection", return_value=connection):
            deleted = repository.delete_asset_purchase(7, 999)

        self.assertFalse(deleted)
        cursor.execute.assert_called_once()

    def test_delete_asset_purchase_returns_the_receipt_filename(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchone.return_value = {"asset_id": 3, "receipt_filename": "3-abc.jpg"}

        with patch.object(repository, "get_connection", return_value=connection):
            deleted = repository.delete_asset_purchase(7, 1)

        query = cursor.execute.call_args_list[0].args[0]
        self.assertIn("RETURNING asset_id, receipt_filename", query)
        self.assertEqual(deleted["receipt_filename"], "3-abc.jpg")

    def test_get_asset_purchases_reports_has_receipt(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchall.return_value = []

        with patch.object(repository, "get_connection", return_value=connection):
            repository.get_asset_purchases(7, 3)

        query = cursor.execute.call_args.args[0]
        self.assertIn("receipt_filename IS NOT NULL AS has_receipt", query)

    def test_get_asset_purchase_is_scoped_to_owner(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchone.return_value = {"id": 1, "asset_id": 3, "receipt_filename": None}

        with patch.object(repository, "get_connection", return_value=connection):
            purchase = repository.get_asset_purchase(7, 1)

        query, parameters = cursor.execute.call_args.args
        self.assertIn("WHERE id = %s", query)
        self.assertIn("AND user_id = %s", query)
        self.assertEqual(parameters, (1, 7))
        self.assertEqual(purchase["asset_id"], 3)

    def test_set_asset_purchase_receipt_is_scoped_to_owner(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchone.return_value = {"id": 1}

        with patch.object(repository, "get_connection", return_value=connection):
            updated = repository.set_asset_purchase_receipt(7, 1, "1-abc.jpg")

        query, parameters = cursor.execute.call_args.args
        self.assertIn("UPDATE portfolio_asset_purchases", query)
        self.assertIn("SET receipt_filename = %s", query)
        self.assertEqual(parameters, ("1-abc.jpg", 1, 7))
        self.assertTrue(updated)
        connection.commit.assert_called_once_with()

    def test_set_asset_purchase_receipt_returns_false_when_not_found(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchone.return_value = None

        with patch.object(repository, "get_connection", return_value=connection):
            updated = repository.set_asset_purchase_receipt(7, 999, "1-abc.jpg")

        self.assertFalse(updated)

    def test_clear_asset_purchase_receipt_is_scoped_to_owner(self):
        connection, cursor = self._connection_and_cursor()
        cursor.fetchone.return_value = {"id": 1}

        with patch.object(repository, "get_connection", return_value=connection):
            updated = repository.clear_asset_purchase_receipt(7, 1)

        query, parameters = cursor.execute.call_args.args
        self.assertIn("SET receipt_filename = NULL", query)
        self.assertEqual(parameters, (1, 7))
        self.assertTrue(updated)


if __name__ == "__main__":
    unittest.main()
