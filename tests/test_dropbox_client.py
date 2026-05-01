"""Unit tests for Dropbox streaming behavior."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dbx2s3.dropbox_client import DropboxClient


class FakeResponse:
    """Response double for streaming download tests."""

    def __init__(self, chunks):
        self._chunks = chunks
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

    def _build_client(self, response: FakeResponse, metadata=None) -> DropboxClient:
        client = DropboxClient.__new__(DropboxClient)
        client.dbx = SimpleNamespace(
            files_download=lambda path: (
                metadata or SimpleNamespace(path_display=path, rev="rev-1", size=5),
                response,
            )
        )
        return client

    def test_download_file_stream_filters_keepalive_chunks_and_closes_response(self) -> None:
        response = FakeResponse([b"abc", b"", b"de"])
        client = self._build_client(response)

        with client.download_file_stream("/docs/file.txt", chunk_size=3) as (metadata, chunks):
            collected = list(chunks)

        self.assertEqual(metadata.path_display, "/docs/file.txt")
        self.assertEqual(collected, [b"abc", b"de"])
        self.assertEqual(response.requested_chunk_size, 3)
        self.assertTrue(response.closed)

    def test_download_file_stream_closes_response_when_iteration_stops_early(self) -> None:
        response = FakeResponse([b"abc", b"def"])
        client = self._build_client(response)

        with client.download_file_stream("/docs/file.txt", chunk_size=3) as (_, chunks):
            next(chunks)

        self.assertTrue(response.closed)

