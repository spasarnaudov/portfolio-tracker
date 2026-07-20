import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASK_APP_DIRECTORY = PROJECT_ROOT / "apps" / "flask"
sys.path.insert(0, str(FLASK_APP_DIRECTORY))
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_ENV", "test")

import api as api_module
import app as application


class MobileApiContractTests(unittest.TestCase):
    def setUp(self):
        application.app.config.update(TESTING=True)
        self.client = application.app.test_client()
        self.user = {
            "id": 7,
            "username": "mobile-user",
            "role": "user",
            "is_deleted": False,
            "active_session_token": "mobile-token",
            "active_session_expires_at": datetime.now() + timedelta(minutes=5),
        }
        self.headers = {"Authorization": "Bearer mobile-token"}

    def auth_patches(self):
        return (
            patch.object(api_module, "get_user_by_session_token", return_value=self.user),
            patch.object(api_module, "update_user_session"),
        )

    def test_health_route_is_registered(self):
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_session_uses_android_wrapper_shape(self):
        auth_user, refresh = self.auth_patches()
        with auth_user, refresh:
            response = self.client.get("/api/v1/auth/session", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["authenticated"])
        self.assertEqual(response.get_json()["user"]["id"], 7)

    def test_asset_prices_use_prices_wrapper(self):
        auth_user, refresh = self.auth_patches()
        with auth_user, refresh, \
                patch.object(api_module, "get_chart_assets", return_value=[{"id": 12}]), \
                patch.object(api_module, "get_latest_price_date", return_value=None), \
                patch.object(api_module, "get_asset_prices", return_value=[]):
            response = self.client.get(
                "/api/v1/assets/12/prices?range=all&interval=daily",
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["prices"], [])

    def test_portfolio_history_uses_points_wrapper(self):
        auth_user, refresh = self.auth_patches()
        with auth_user, refresh, \
                patch.object(api_module, "get_latest_price_date", return_value=None), \
                patch.object(api_module, "get_portfolio_history", return_value=[]):
            response = self.client.get(
                "/api/v1/portfolio/history?range=all&interval=daily",
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["points"], [])

    def test_old_assumed_account_route_returns_404_json(self):
        response = self.client.get("/api/v1/account/me")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"]["code"], "not_found")


if __name__ == "__main__":
    unittest.main()
