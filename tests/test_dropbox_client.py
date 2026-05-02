"""Unit tests for Dropbox streaming behavior."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import dropbox

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dbx2s3.dropbox_client import DropboxClient


class FakeFileMetadata:
    """Minimal Dropbox file metadata for list tests."""

    def __init__(self, path_display: str, rev: str = "rev-1", size: int = 5):
        self.path_display = path_display
        self.rev = rev
        self.size = size


class FakeResponse:
    """Response double for streaming download tests."""

    def __init__(self, chunks, content=None):
        self._chunks = chunks
        self.content = content if content is not None else b"".join(chunks)
        self.closed = False
        self.requested_chunk_size = None

    def iter_content(self, chunk_size):
        self.requested_chunk_size = chunk_size
        for chunk in self._chunks:
            yield chunk

    def close(self) -> None:
        self.closed = True


class DropboxClientStreamTests(unittest.TestCase):
    """Exercises chunk filtering and cleanup semantics."""

    def _build_client(self, dbx) -> tuple[DropboxClient, list[float]]:
        sleep_calls: list[float] = []
        client = DropboxClient.__new__(DropboxClient)
        client.dbx = dbx
        client.retry_max_attempts = 3
        client.retry_base_delay = 1.0
        client.retry_max_delay = 60.0
        client.retry_jitter_ratio = 0.25
        client._sleep = sleep_calls.append
        client._random = lambda: 0.0
        return client, sleep_calls

    def test_download_file_stream_filters_keepalive_chunks_and_closes_response(self) -> None:
        response = FakeResponse([b"abc", b"", b"de"])
        client, _ = self._build_client(
            SimpleNamespace(
                files_download=lambda path: (
                    SimpleNamespace(path_display=path, rev="rev-1", size=5),
                    response,
                )
            )
        )

        with client.download_file_stream("/docs/file.txt", chunk_size=3) as (metadata, chunks):
            collected = list(chunks)

        self.assertEqual(metadata.path_display, "/docs/file.txt")
        self.assertEqual(collected, [b"abc", b"de"])
        self.assertEqual(response.requested_chunk_size, 3)
        self.assertTrue(response.closed)

    def test_download_file_stream_closes_response_when_iteration_stops_early(self) -> None:
        response = FakeResponse([b"abc", b"def"])
        client, _ = self._build_client(
            SimpleNamespace(
                files_download=lambda path: (
                    SimpleNamespace(path_display=path, rev="rev-1", size=5),
                    response,
                )
            )
        )

        with client.download_file_stream("/docs/file.txt", chunk_size=3) as (_, chunks):
            next(chunks)

        self.assertTrue(response.closed)

    def test_list_all_files_retries_rate_limit_with_server_backoff(self) -> None:
        metadata = FakeFileMetadata("/docs/file.txt")
        responses = iter(
            [
                dropbox.exceptions.RateLimitError("req-1", backoff=4),
                SimpleNamespace(entries=[metadata], has_more=False),
            ]
        )

        def files_list_folder(path, recursive):
            result = next(responses)
            if isinstance(result, Exception):
                raise result
            return result

        client, sleep_calls = self._build_client(
            SimpleNamespace(files_list_folder=files_list_folder)
        )

        with patch("dbx2s3.dropbox_client.FileMetadata", FakeFileMetadata):
            files = list(client.list_all_files("/docs"))

        self.assertEqual([file.path_display for file in files], ["/docs/file.txt"])
        self.assertEqual(sleep_calls, [4.0])

    def test_download_file_retries_transient_http_errors_with_backoff(self) -> None:
        responses = iter(
            [
                dropbox.exceptions.InternalServerError("req-1", 500, None),
                (
                    SimpleNamespace(path_display="/docs/file.txt", rev="rev-1", size=3),
                    FakeResponse([b"abc"]),
                ),
            ]
        )

        def files_download(path):
            result = next(responses)
            if isinstance(result, Exception):
                raise result
            return result

        client, sleep_calls = self._build_client(
            SimpleNamespace(files_download=files_download)
        )

        content, metadata = client.download_file("/docs/file.txt")

        self.assertEqual(content, b"abc")
        self.assertEqual(metadata.path_display, "/docs/file.txt")
        self.assertEqual(sleep_calls, [1.0])

    def test_download_file_does_not_retry_auth_errors(self) -> None:
        attempts = {"count": 0}

        def files_download(path):
            attempts["count"] += 1
            raise dropbox.exceptions.AuthError("req-1", "invalid token")

        client, sleep_calls = self._build_client(
            SimpleNamespace(files_download=files_download)
        )

        with self.assertRaises(dropbox.exceptions.AuthError):
            client.download_file("/docs/file.txt")

        self.assertEqual(attempts["count"], 1)
        self.assertEqual(sleep_calls, [])

