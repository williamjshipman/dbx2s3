"""Basic tests and test suite entrypoint for dbx2s3."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
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


def load_test_suite() -> unittest.TestSuite:
    """Load the complete test suite for local runs and CI."""
    return unittest.defaultTestLoader.discover(
        start_dir=str(Path(__file__).parent),
        pattern="test_*.py",
    )


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(load_test_suite())
    raise SystemExit(0 if result.wasSuccessful() else 1)
