import io
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

import api as api_module
import app as application
import receipts as receipts_module


class PurchaseReceiptTests(unittest.TestCase):
    def setUp(self):
        application.app.config.update(TESTING=True)
        self.client = application.app.test_client()
        self.user = {
            "id": 7,
            "username": "receipt-user",
            "role": "user",
            "is_deleted": False,
            "active_session_token": "receipt-token",
            "active_session_expires_at": datetime.now() + timedelta(minutes=5),
        }
        self.headers = {"Authorization": "Bearer receipt-token"}

        self.tmp_dir = tempfile.TemporaryDirectory()
        self.uploads_dir = Path(self.tmp_dir.name)
        self._uploads_patches = (
            patch.object(api_module, "UPLOADS_DIR", self.uploads_dir),
            patch.object(receipts_module, "UPLOADS_DIR", self.uploads_dir),
        )
        for uploads_patch in self._uploads_patches:
            uploads_patch.start()

    def tearDown(self):
        for uploads_patch in self._uploads_patches:
            uploads_patch.stop()
        self.tmp_dir.cleanup()

    def auth_patches(self):
        return (
            patch.object(api_module, "get_user_by_session_token", return_value=self.user),
            patch.object(api_module, "update_user_session"),
        )

    def test_upload_then_fetch_then_delete_round_trips_the_file(self):
        auth_user, refresh = self.auth_patches()
        fake_image = b"\xff\xd8\xff fake jpeg bytes"

        with auth_user, refresh, \
                patch.object(api_module, "get_asset_purchase", return_value={"id": 1, "asset_id": 3, "receipt_filename": None}), \
                patch.object(api_module, "set_asset_purchase_receipt", return_value=True):
            upload_response = self.client.post(
                "/api/v1/portfolio/purchases/1/receipt",
                headers=self.headers,
                data={"receipt": (io.BytesIO(fake_image), "receipt.jpg")},
            )

        self.assertEqual(upload_response.status_code, 201)
        self.assertTrue(upload_response.get_json()["has_receipt"])

        saved_files = list(self.uploads_dir.iterdir())
        self.assertEqual(len(saved_files), 1)
        self.assertTrue(saved_files[0].name.startswith("1-"))
        self.assertEqual(saved_files[0].read_bytes(), fake_image)
        saved_filename = saved_files[0].name

        with auth_user, refresh, \
                patch.object(api_module, "get_asset_purchase", return_value={"id": 1, "asset_id": 3, "receipt_filename": saved_filename}):
            fetch_response = self.client.get("/api/v1/portfolio/purchases/1/receipt", headers=self.headers)

        self.assertEqual(fetch_response.status_code, 200)
        self.assertEqual(fetch_response.data, fake_image)
        fetch_response.close()

        with auth_user, refresh, \
                patch.object(api_module, "get_asset_purchase", return_value={"id": 1, "asset_id": 3, "receipt_filename": saved_filename}), \
                patch.object(api_module, "clear_asset_purchase_receipt", return_value=True):
            delete_response = self.client.delete("/api/v1/portfolio/purchases/1/receipt", headers=self.headers)

        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(list(self.uploads_dir.iterdir()), [])

    def test_upload_rejects_disallowed_extension(self):
        auth_user, refresh = self.auth_patches()

        with auth_user, refresh, \
                patch.object(api_module, "get_asset_purchase", return_value={"id": 1, "asset_id": 3, "receipt_filename": None}):
            response = self.client.post(
                "/api/v1/portfolio/purchases/1/receipt",
                headers=self.headers,
                data={"receipt": (io.BytesIO(b"not an image"), "receipt.txt")},
            )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(list(self.uploads_dir.iterdir()), [])

    def test_upload_404s_when_purchase_not_owned(self):
        auth_user, refresh = self.auth_patches()

        with auth_user, refresh, \
                patch.object(api_module, "get_asset_purchase", return_value=None):
            response = self.client.post(
                "/api/v1/portfolio/purchases/1/receipt",
                headers=self.headers,
                data={"receipt": (io.BytesIO(b"bytes"), "receipt.jpg")},
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(list(self.uploads_dir.iterdir()), [])

    def test_fetch_receipt_404s_when_none_uploaded(self):
        auth_user, refresh = self.auth_patches()

        with auth_user, refresh, \
                patch.object(api_module, "get_asset_purchase", return_value={"id": 1, "asset_id": 3, "receipt_filename": None}):
            response = self.client.get("/api/v1/portfolio/purchases/1/receipt", headers=self.headers)

        self.assertEqual(response.status_code, 404)

    def test_upload_replaces_the_previous_file(self):
        auth_user, refresh = self.auth_patches()
        old_file = self.uploads_dir / "1-old.jpg"
        old_file.write_bytes(b"old bytes")

        with auth_user, refresh, \
                patch.object(api_module, "get_asset_purchase", return_value={"id": 1, "asset_id": 3, "receipt_filename": "1-old.jpg"}), \
                patch.object(api_module, "set_asset_purchase_receipt", return_value=True):
            response = self.client.post(
                "/api/v1/portfolio/purchases/1/receipt",
                headers=self.headers,
                data={"receipt": (io.BytesIO(b"new bytes"), "receipt.png")},
            )

        self.assertEqual(response.status_code, 201)
        remaining_files = list(self.uploads_dir.iterdir())
        self.assertEqual(len(remaining_files), 1)
        self.assertFalse(old_file.exists())


if __name__ == "__main__":
    unittest.main()
