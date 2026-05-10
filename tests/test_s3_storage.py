"""Unit tests for streaming storage helpers."""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dbx2s3.s3_storage import ChunkIteratorIO, S3Storage


class ChunkIteratorIOTests(unittest.TestCase):
    """Validates buffering behavior for iterator-backed streams."""

    def test_chunk_iterator_io_reads_across_chunk_boundaries(self) -> None:
        stream = io.BufferedReader(ChunkIteratorIO(iter([b"ab", b"cd", b"ef"])))

        self.assertEqual(stream.read(5), b"abcde")
        self.assertEqual(stream.read(), b"f")
        self.assertEqual(stream.read(), b"")

    def test_chunk_iterator_io_skips_empty_chunks(self) -> None:
        """Empty chunks must not cause an infinite loop and must be ignored."""
        stream = io.BufferedReader(ChunkIteratorIO(iter([b"", b"hello", b"", b" world"])))

        self.assertEqual(stream.read(), b"hello world")


class S3StorageUploadTests(unittest.TestCase):
    """Ensures iterable uploads are streamed through boto3 correctly."""

    def test_upload_file_wraps_iterable_sources_and_stringifies_metadata(self) -> None:
        storage = S3Storage.__new__(S3Storage)
        storage.bucket = "backup-bucket"
        storage.s3 = Mock()
        uploaded_payload = {}

        def capture_upload(fileobj, bucket, key, **kwargs) -> None:
            uploaded_payload["body"] = fileobj.read()
            uploaded_payload["bucket"] = bucket
            uploaded_payload["key"] = key
            uploaded_payload["extra_args"] = kwargs["ExtraArgs"]

        storage.s3.upload_fileobj.side_effect = capture_upload

        storage.upload_file(
            "docs/file.txt",
            iter([b"ab", b"cd"]),
            {"dropbox_size": 4, "is_partial": False},
        )

        storage.s3.upload_fileobj.assert_called_once()
        self.assertEqual(uploaded_payload["body"], b"abcd")
        self.assertEqual(uploaded_payload["bucket"], "backup-bucket")
        self.assertEqual(uploaded_payload["key"], "docs/file.txt")
        self.assertEqual(
            uploaded_payload["extra_args"],
            {"Metadata": {"dropbox_size": "4", "is_partial": "False"}},
        )


class S3StorageInitTests(unittest.TestCase):
    """Ensures Session setup supports IAM/default credential chain."""

    def test_init_without_explicit_credentials_uses_default_session_chain(self) -> None:
        session = Mock()
        session.client.return_value = Mock()

        with patch("dbx2s3.s3_storage.boto3.Session", return_value=session) as session_ctor:
            with patch.object(S3Storage, "_ensure_bucket_exists") as ensure_bucket:
                S3Storage(bucket="backup-bucket", region="us-east-1")

        session_ctor.assert_called_once_with(region_name="us-east-1")
        ensure_bucket.assert_called_once()
