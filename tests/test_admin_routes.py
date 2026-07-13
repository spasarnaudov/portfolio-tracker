import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASK_APP_DIRECTORY = PROJECT_ROOT / "apps" / "flask"
sys.path.insert(0, str(FLASK_APP_DIRECTORY))
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_ENV", "test")

import app as application


class AdminRouteTests(unittest.TestCase):
    def setUp(self):
        application.app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = application.app.test_client()

    def _set_session(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["username"] = "tester"
            session["session_token"] = "token"

    def _user(self, role):
        return {
            "id": 1,
            "username": "tester",
            "role": role,
            "is_active": True,
            "active_session_token": "token",
            "active_session_expires_at": datetime.now() + timedelta(minutes=5),
        }

    def _get_as(self, path, role):
        self._set_session()
        with patch.object(application, "get_user_by_id", return_value=self._user(role)), \
                patch.object(application, "update_user_session"):
            return self.client.get(path)

    def test_unauthenticated_user_is_redirected_from_admin_pages(self):
        for path in ("/admin/users", "/admin/logs"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.location)

    def test_non_admin_is_redirected_from_admin_pages(self):
        for path in ("/admin/users", "/admin/logs"):
            response = self._get_as(path, "user")
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.endswith("/portfolio"))

    def test_regular_user_home_redirects_to_portfolio(self):
        response = self._get_as("/", "user")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/portfolio"))

    def test_charts_page_is_removed(self):
        response = self._get_as("/charts", "user")

        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_users(self):
        listed_user = self._user("admin") | {
            "created_at": datetime(2026, 7, 14, 12, 34, 56, 789123),
        }

        with patch.object(application, "get_users", return_value=[listed_user]):
            response = self._get_as("/admin/users", "admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Users", response.data)
        self.assertNotIn(b">Portfolio<", response.data)
        self.assertNotIn(b">Charts<", response.data)
        self.assertNotIn(b'value="demo"', response.data)
        self.assertIn(b"2026-07-14 12:34:56", response.data)
        self.assertNotIn(b"789123", response.data)

    def test_admin_can_view_logs_and_content_is_html_escaped(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "logs").mkdir()
            (root / "logs" / "audit.log").write_text("<script>alert(1)</script>\n", encoding="utf-8")

            with patch.object(application, "PROJECT_ROOT", root):
                response = self._get_as("/admin/logs", "admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"audit.log", response.data)
        self.assertIn(b"&lt;script&gt;", response.data)
        self.assertNotIn(b"<script>alert(1)</script>", response.data)

    def test_missing_and_empty_log_directories_have_messages(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with patch.object(application, "PROJECT_ROOT", root):
                missing_response = self._get_as("/admin/logs", "admin")

            (root / "logs").mkdir()
            with patch.object(application, "PROJECT_ROOT", root):
                empty_response = self._get_as("/admin/logs", "admin")

        self.assertIn(b"Log directory not found.", missing_response.data)
        self.assertIn(b"No log files found.", empty_response.data)

    def test_portfolio_saves_chart_selection_for_tavex_and_manual_items(self):
        self._set_session()
        form_data = {
            "quantity_7": "2",
            "quantity_8": "3",
            "holding_include_in_chart": "7",
            "manual_item_id": "9",
            "manual_item_name": "Gold ring",
            "manual_item_quantity": "3.5",
            "manual_item_unit_price": "80",
            "manual_item_include_in_chart": "9",
        }

        with patch.object(application, "get_user_by_id", return_value=self._user("user")), \
                patch.object(application, "update_user_session"), \
                patch.object(application, "save_portfolio_holdings") as save_holdings, \
                patch.object(application, "save_portfolio_manual_items") as save_manual_items:
            response = self.client.post("/portfolio", data=form_data)

        self.assertEqual(response.status_code, 302)
        save_holdings.assert_called_once_with(1, {7: 2.0, 8: 3.0}, {7})
        save_manual_items.assert_called_once_with(1, [{
            "id": 9,
            "name": "Gold ring",
            "quantity": 3.5,
            "unit_price": 80.0,
            "include_in_chart": True,
            "delete": False,
        }])

    def test_portfolio_excludes_zero_quantity_items_from_chart(self):
        self._set_session()
        form_data = {
            "quantity_7": "0",
            "holding_include_in_chart": "7",
            "manual_item_id": "9",
            "manual_item_name": "Gold ring",
            "manual_item_quantity": "0",
            "manual_item_unit_price": "80",
            "manual_item_include_in_chart": "9",
        }

        with patch.object(application, "get_user_by_id", return_value=self._user("user")), \
                patch.object(application, "update_user_session"), \
                patch.object(application, "save_portfolio_holdings") as save_holdings, \
                patch.object(application, "save_portfolio_manual_items") as save_manual_items:
            response = self.client.post("/portfolio", data=form_data)

        self.assertEqual(response.status_code, 302)
        save_holdings.assert_called_once_with(1, {7: 0.0}, set())
        save_manual_items.assert_called_once_with(1, [{
            "id": 9,
            "name": "Gold ring",
            "quantity": 0.0,
            "unit_price": 80.0,
            "include_in_chart": False,
            "delete": False,
        }])

    def test_portfolio_ajax_save_returns_updated_chart_without_redirect(self):
        self._set_session()
        price_date = datetime(2026, 7, 13, 12, 0)

        with patch.object(application, "get_user_by_id", return_value=self._user("user")), \
                patch.object(application, "update_user_session"), \
                patch.object(application, "save_portfolio_holdings"), \
                patch.object(application, "save_portfolio_manual_items"), \
                patch.object(application, "get_dashboard_summary", return_value={
                    "latest_price_date": price_date,
                }), \
                patch.object(application, "get_portfolio_history", return_value=[{
                    "price_date": price_date,
                    "value": 123.45,
                }]):
            response = self.client.post(
                "/portfolio?portfolio_range=1d&portfolio_interval=hourly",
                data={"quantity_7": "2", "holding_include_in_chart": "7"},
                headers={"X-Requested-With": "XMLHttpRequest"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["chart_values"], [123.45])
        self.assertEqual(response.json["portfolio_interval"], "hourly")


if __name__ == "__main__":
    unittest.main()
