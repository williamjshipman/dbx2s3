"""Dropbox client for enumerating and downloading files.

This module provides both traditional and streaming download methods:
- download_file: Loads entire file into memory (for small files)
- download_file_stream: Streams file in chunks (for large files >100MB)
"""

import logging
import random
import time
from contextlib import contextmanager
from typing import Callable, Iterator, Tuple, TypeVar

import dropbox
from dropbox.files import FileMetadata, FolderMetadata
from requests import exceptions as requests_exceptions


logger = logging.getLogger(__name__)
T = TypeVar("T")


class DropboxClient:
    """Client for interacting with Dropbox API."""
    
    def __init__(
        self,
        access_token: str,
        retry_max_attempts: int = 3,
        retry_base_delay: float = 1.0,
        sleep_func: Callable[[float], None] = time.sleep,
        random_func: Callable[[], float] = random.random,
    ):
        """Initialize Dropbox client.
        
        Args:
            access_token: Dropbox access token
            retry_max_attempts: Maximum attempts for retryable Dropbox operations
            retry_base_delay: Base delay in seconds for exponential backoff
        """
        self.dbx = dropbox.Dropbox(access_token)
        self.retry_max_attempts = retry_max_attempts
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = 60.0
        self.retry_jitter_ratio = 0.25
        self._sleep = sleep_func
        self._random = random_func

    def _call_with_retry(self, operation: str, func: Callable[[], T]) -> T:
        """Run a Dropbox operation with retries for transient failures."""
        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                return func()
            except Exception as error:
                if not self._is_retryable_error(error) or attempt >= self.retry_max_attempts:
                    raise

                delay = self._get_retry_delay(error, attempt)
                logger.warning(
                    "dropbox_retrying",
                    extra={
                        "operation": operation,
                        "attempt": attempt,
                        "max_attempts": self.retry_max_attempts,
                        "delay_seconds": delay,
                        "error_type": type(error).__name__,
                    },
                )
                self._sleep(delay)

        raise RuntimeError("Retry loop exited unexpectedly")

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine whether a Dropbox operation error is retryable."""
        if isinstance(error, dropbox.exceptions.AuthError):
            return False

        if isinstance(error, dropbox.exceptions.RateLimitError):
            return True

        if isinstance(error, dropbox.exceptions.InternalServerError):
            return True

        if isinstance(error, dropbox.exceptions.HttpError):
            return error.status_code in {408, 429, 500, 502, 503, 504}

        if isinstance(error, requests_exceptions.RequestException):
            return True

        return isinstance(error, TimeoutError)

    def _get_retry_delay(self, error: Exception, attempt: int) -> float:
        """Get the next retry delay for a retryable Dropbox error."""
        if isinstance(error, dropbox.exceptions.RateLimitError) and error.backoff:
            return float(error.backoff)

        base_delay = min(
            self.retry_base_delay * (2 ** (attempt - 1)),
            self.retry_max_delay,
        )
        jitter = base_delay * self.retry_jitter_ratio * self._random()
        return min(base_delay + jitter, self.retry_max_delay)

    def _download_file_once(self, path: str) -> Tuple[bytes, FileMetadata]:
        """Download a Dropbox file fully and close the response."""
        response = None
        try:
            metadata, response = self.dbx.files_download(path)
            return response.content, metadata
        finally:
            if response is not None:
                response.close()
        
    def list_all_files(self, path: str = "") -> Iterator[FileMetadata]:
        """Recursively list all files in Dropbox.
        
        Args:
            path: Starting path (empty string for root)
            
        Yields:
            FileMetadata objects for each file
        """
        try:
            result = self._call_with_retry(
                "files_list_folder",
                lambda: self.dbx.files_list_folder(path, recursive=True),
            )
            
            while True:
                for entry in result.entries:
                    if isinstance(entry, FileMetadata):
                        logger.debug(f"Found file: {entry.path_display}")
                        yield entry
                
                if not result.has_more:
                    break
                    
                result = self._call_with_retry(
                    "files_list_folder_continue",
                    lambda: self.dbx.files_list_folder_continue(result.cursor),
                )
                
        except (
            dropbox.exceptions.DropboxException,
            requests_exceptions.RequestException,
            TimeoutError,
        ) as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    def download_file(self, path: str) -> Tuple[bytes, FileMetadata]:
        """Download a file from Dropbox (loads entire file into memory).

        Note: For files >100MB, prefer download_file_stream() to avoid
        memory exhaustion.

        Args:
            path: Path to the file in Dropbox

        Returns:
            Tuple of (file content as bytes, file metadata)
        """
        try:
            content, metadata = self._call_with_retry(
                "files_download",
                lambda: self._download_file_once(path),
            )
            logger.debug(
                "dropbox_download_complete",
                extra={"path": path, "size_bytes": len(content)}
            )
            return content, metadata
        except (
            dropbox.exceptions.DropboxException,
            requests_exceptions.RequestException,
            TimeoutError,
        ) as e:
            logger.error(
                "dropbox_download_failed",
                extra={"path": path, "error": str(e)},
                exc_info=True
            )
            raise

    @contextmanager
    def download_file_stream(self, path: str, chunk_size: int = 8 * 1024 * 1024):
        """Download a file from Dropbox as a stream (memory-efficient).

        Uses chunked streaming to handle large files without loading
        entire contents into memory. Recommended for files >100MB.

        Args:
            path: Path to the file in Dropbox
            chunk_size: Size of each chunk in bytes (default: 8MB)

        Yields:
            Tuple of (FileMetadata, Iterator[bytes]) where the iterator
            yields chunks of the specified size

        Example:
            >>> with client.download_file_stream("/large_file.bin") as (metadata, chunks):
            ...     for chunk in chunks:
            ...         process(chunk)

        Note:
            The response must be consumed within the context manager to
            ensure proper cleanup of network resources.
        """
        response = None
        try:
            metadata, response = self._call_with_retry(
                "files_download_stream",
                lambda: self.dbx.files_download(path),
            )

            def chunk_iterator():
                """Generator that yields file chunks."""
                bytes_downloaded = 0
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # Filter out keep-alive chunks
                        bytes_downloaded += len(chunk)
                        yield chunk

                logger.debug(
                    "dropbox_stream_complete",
                    extra={
                        "path": path,
                        "size_bytes": bytes_downloaded,
                        "chunk_size": chunk_size
                    }
                )

            yield metadata, chunk_iterator()

        except (
            dropbox.exceptions.DropboxException,
            requests_exceptions.RequestException,
            TimeoutError,
        ) as e:
            logger.error(
                "dropbox_stream_failed",
                extra={"path": path, "error": str(e)},
                exc_info=True
            )
            raise
        finally:
            # Ensure response is closed to release network resources
            if response is not None:
                try:
                    response.close()
                except Exception as e:
                    logger.warning(
                        "dropbox_response_close_failed",
                        extra={"error": str(e)}
                    )

    
    def get_file_metadata(self, path: str) -> FileMetadata:
        """Get metadata for a file.
        
        Args:
            path: Path to the file in Dropbox
            
        Returns:
            FileMetadata object
        """
        try:
            metadata = self.dbx.files_get_metadata(path)
            if not isinstance(metadata, FileMetadata):
                raise ValueError(f"{path} is not a file")
            return metadata
        except dropbox.exceptions.ApiError as e:
            logger.error(f"Error getting metadata for {path}: {e}")
            raise
