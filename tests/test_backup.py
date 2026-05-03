"""Unit tests for backup orchestration."""

from __future__ import annotations

import sys
import unittest
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dbx2s3.backup import BackupManager


@dataclass
class FakeFileMetadata:
    """Minimal Dropbox metadata used by BackupManager."""

    path_display: str
    rev: str
    size: int
    server_modified: datetime | None = None
    content_hash: str | None = None


class FakeDropboxClient:
    """Dropbox double for predictable backup tests."""

    def __init__(
        self,
        listed_files: list[FakeFileMetadata],
        downloads: dict[str, tuple[FakeFileMetadata, Iterable[bytes]]],
    ) -> None:
        self._listed_files = listed_files
        self._downloads = downloads
        self.downloaded_paths: list[str] = []

    def list_all_files(self, path: str = "") -> Iterable[FakeFileMetadata]:
        self.last_list_path = path
        return iter(self._listed_files)

    @contextmanager
    def download_file_stream(self, path: str):
        self.downloaded_paths.append(path)
        metadata, chunks = self._downloads[path]
        yield metadata, iter(chunks)


class FakeStorage:
    """Storage double that records uploads and can fail selected keys."""

    def __init__(self, failing_keys: set[str] | None = None) -> None:
        self.failing_keys = failing_keys or set()
        self.upload_calls: list[dict[str, object]] = []

    def upload_file(self, key, data, metadata=None) -> None:
        if key in self.failing_keys:
            raise RuntimeError(f"upload failed for {key}")

        payload = b"".join(data)
        self.upload_calls.append(
            {
                "key": key,
                "payload": payload,
                "metadata": metadata,
            }
        )


class FakeStateManager:
    """State manager double with controllable skip decisions."""

    def __init__(self, should_backup: dict[str, bool] | None = None) -> None:
        self.should_backup = should_backup or {}
        self.should_backup_calls: list[tuple[str, str, int]] = []
        self.marked_files: list[tuple[str, str, int, str | None]] = []

    def should_backup_file(self, path: str, rev: str, size: int) -> bool:
        self.should_backup_calls.append((path, rev, size))
        return self.should_backup.get(path, True)

    def mark_file_backed_up(
        self,
        path: str,
        rev: str,
        size: int,
        content_hash: str | None = None,
    ) -> None:
        self.marked_files.append((path, rev, size, content_hash))


class BackupManagerTests(unittest.TestCase):
    """Covers success, skip, and failure paths in backup orchestration."""

    def test_backup_uploads_changed_files_and_records_state(self) -> None:
        listed_file = FakeFileMetadata("/docs/report.txt", "listing-rev", 5)
        downloaded_metadata = FakeFileMetadata(
            "/docs/report.txt",
            "downloaded-rev",
            5,
            server_modified=datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            content_hash="hash-123",
        )
        dropbox = FakeDropboxClient(
            [listed_file],
            {"/docs/report.txt": (downloaded_metadata, [b"he", b"llo"])},
        )
        storage = FakeStorage()
        state = FakeStateManager()

        manager = BackupManager(dropbox, storage, state)

        stats = manager.backup(path="/docs", resume=True)

        self.assertEqual(
            stats,
            {"total_files": 1, "backed_up": 1, "skipped": 0, "errors": 0},
        )
        self.assertEqual(dropbox.last_list_path, "/docs")
        self.assertEqual(dropbox.downloaded_paths, ["/docs/report.txt"])
        self.assertEqual(state.should_backup_calls, [("/docs/report.txt", "listing-rev", 5)])
        self.assertEqual(
            state.marked_files,
            [("/docs/report.txt", "downloaded-rev", 5, "hash-123")],
        )
        self.assertEqual(len(storage.upload_calls), 1)
        self.assertEqual(storage.upload_calls[0]["key"], "docs/report.txt")
        self.assertEqual(storage.upload_calls[0]["payload"], b"hello")
        self.assertEqual(
            storage.upload_calls[0]["metadata"],
            {
                "dropbox_path": "/docs/report.txt",
                "dropbox_rev": "downloaded-rev",
                "dropbox_size": "5",
                "dropbox_modified": "2024-01-02T03:04:05+00:00",
            },
        )

    def test_backup_skips_unchanged_files_when_resume_enabled(self) -> None:
        listed_file = FakeFileMetadata("/docs/report.txt", "rev-1", 5)
        dropbox = FakeDropboxClient([listed_file], {})
        storage = FakeStorage()
        state = FakeStateManager(should_backup={"/docs/report.txt": False})

        manager = BackupManager(dropbox, storage, state)

        stats = manager.backup(resume=True)

        self.assertEqual(
            stats,
            {"total_files": 1, "backed_up": 0, "skipped": 1, "errors": 0},
        )
        self.assertEqual(dropbox.downloaded_paths, [])
        self.assertEqual(storage.upload_calls, [])
        self.assertEqual(state.marked_files, [])

    def test_backup_continues_after_upload_error_and_does_not_mark_failed_file(self) -> None:
        failed_file = FakeFileMetadata("/docs/bad.txt", "bad-rev", 3)
        good_file = FakeFileMetadata("/docs/good.txt", "good-rev", 4)
        server_modified = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        dropbox = FakeDropboxClient(
            [failed_file, good_file],
            {
                "/docs/bad.txt": (
                    FakeFileMetadata("/docs/bad.txt", "bad-rev", 3, server_modified),
                    [b"bad"],
                ),
                "/docs/good.txt": (
                    FakeFileMetadata(
                        "/docs/good.txt",
                        "good-rev",
                        4,
                        server_modified,
                        "good-hash",
                    ),
                    [b"go", b"od"],
                ),
            },
        )
        storage = FakeStorage(failing_keys={"docs/bad.txt"})
        state = FakeStateManager()

        manager = BackupManager(dropbox, storage, state)

        stats = manager.backup(resume=False)

        self.assertEqual(
            stats,
            {"total_files": 2, "backed_up": 1, "skipped": 0, "errors": 1},
        )
        self.assertEqual(state.should_backup_calls, [])
        self.assertEqual(
            state.marked_files,
            [("/docs/good.txt", "good-rev", 4, "good-hash")],
        )
        self.assertEqual(len(storage.upload_calls), 1)
        self.assertEqual(storage.upload_calls[0]["key"], "docs/good.txt")

