"""Basic tests and test suite entrypoint for dbx2s3."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dbx2s3.config import Config
from dbx2s3.state_manager import StateManager


class StateManagerTests(unittest.TestCase):
    """Test state manager functionality."""

    def test_state_manager_tracks_and_persists_file_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = str(Path(temp_dir) / "state.json")

            manager = StateManager(state_file)

            self.assertTrue(manager.should_backup_file("/test.txt", "rev1", 100))

            manager.mark_file_backed_up("/test.txt", "rev1", 100)

            self.assertFalse(manager.should_backup_file("/test.txt", "rev1", 100))
            self.assertTrue(manager.should_backup_file("/test.txt", "rev2", 100))
            self.assertTrue(manager.should_backup_file("/test.txt", "rev1", 200))

            state = manager.get_file_state("/test.txt")
            self.assertIsNotNone(state)
            self.assertEqual(state["rev"], "rev1")
            self.assertEqual(state["size"], 100)

            manager2 = StateManager(state_file)
            self.assertFalse(manager2.should_backup_file("/test.txt", "rev1", 100))


class ConfigTests(unittest.TestCase):
    """Test configuration validation."""

    def test_missing_dropbox_token_raises_value_error(self) -> None:
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "DROPBOX_TOKEN"):
                Config.from_env()

    def test_config_loads_dropbox_retry_settings(self) -> None:
        with unittest.mock.patch.dict(
            os.environ,
            {
                "DROPBOX_TOKEN": "token",
                "STORAGE_TYPE": "s3",
                "S3_ACCESS_KEY": "key",
                "S3_SECRET_KEY": "secret",
                "S3_BUCKET": "bucket",
                "DROPBOX_RETRY_MAX_ATTEMPTS": "5",
                "DROPBOX_RETRY_BASE_DELAY": "2.5",
            },
            clear=True,
        ):
            config = Config.from_env()

        self.assertEqual(config.dropbox_retry_max_attempts, 5)
        self.assertEqual(config.dropbox_retry_base_delay, 2.5)

    def test_invalid_dropbox_retry_settings_raise_value_error(self) -> None:
        invalid_cases = [
            ("DROPBOX_RETRY_MAX_ATTEMPTS", "0"),
            ("DROPBOX_RETRY_MAX_ATTEMPTS", "invalid"),
            ("DROPBOX_RETRY_BASE_DELAY", "0"),
            ("DROPBOX_RETRY_BASE_DELAY", "-1"),
            ("DROPBOX_RETRY_BASE_DELAY", "invalid"),
        ]

        for name, value in invalid_cases:
            with self.subTest(name=name, value=value):
                with unittest.mock.patch.dict(
                    os.environ,
                    {
                        "DROPBOX_TOKEN": "token",
                        "STORAGE_TYPE": "s3",
                        "S3_ACCESS_KEY": "key",
                        "S3_SECRET_KEY": "secret",
                        "S3_BUCKET": "bucket",
                        name: value,
                    },
                    clear=True,
                ):
                    with self.assertRaisesRegex(ValueError, name):
                        Config.from_env()

    def test_aws_config_allows_iam_auth_without_explicit_keys(self) -> None:
        with unittest.mock.patch.dict(
            os.environ,
            {
                "DROPBOX_TOKEN": "token",
                "STORAGE_TYPE": "aws",
                "S3_BUCKET": "bucket",
            },
            clear=True,
        ):
            config = Config.from_env()

        self.assertIsNone(config.s3_access_key)
        self.assertIsNone(config.s3_secret_key)
        self.assertEqual(config.s3_bucket, "bucket")

    def test_s3_endpoint_requires_explicit_credentials(self) -> None:
        with unittest.mock.patch.dict(
            os.environ,
            {
                "DROPBOX_TOKEN": "token",
                "STORAGE_TYPE": "s3",
                "S3_ENDPOINT": "https://minio.example.com",
                "S3_BUCKET": "bucket",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "S3_ACCESS_KEY and S3_SECRET_KEY"):
                Config.from_env()


def load_test_suite() -> unittest.TestSuite:
    """Load the complete test suite for local runs and CI."""
    return unittest.defaultTestLoader.discover(
        start_dir=str(Path(__file__).parent),
        pattern="test_*.py",
    )


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(load_test_suite())
    raise SystemExit(0 if result.wasSuccessful() else 1)
