"""Dropbox client for enumerating and downloading files.

This module provides both traditional and streaming download methods:
- download_file: Loads entire file into memory (for small files)
- download_file_stream: Streams file in chunks (for large files >100MB)
"""

import logging
from contextlib import contextmanager
from typing import Iterator, Tuple
import dropbox
from dropbox.files import FileMetadata, FolderMetadata


logger = logging.getLogger(__name__)


class DropboxClient:
    """Client for interacting with Dropbox API."""
    
    def __init__(self, access_token: str):
        """Initialize Dropbox client.
        
        Args:
            access_token: Dropbox access token
        """
        self.dbx = dropbox.Dropbox(access_token)
        
    def list_all_files(self, path: str = "") -> Iterator[FileMetadata]:
        """Recursively list all files in Dropbox.
        
        Args:
            path: Starting path (empty string for root)
            
        Yields:
            FileMetadata objects for each file
        """
        try:
            result = self.dbx.files_list_folder(path, recursive=True)
            
            while True:
                for entry in result.entries:
                    if isinstance(entry, FileMetadata):
                        logger.debug(f"Found file: {entry.path_display}")
                        yield entry
                
                if not result.has_more:
                    break
                    
                result = self.dbx.files_list_folder_continue(result.cursor)
                
        except dropbox.exceptions.ApiError as e:
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
            metadata, response = self.dbx.files_download(path)
            content = response.content
            logger.debug(
                "dropbox_download_complete",
                extra={"path": path, "size_bytes": len(content)}
            )
            return content, metadata
        except dropbox.exceptions.ApiError as e:
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
            metadata, response = self.dbx.files_download(path)

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

        except dropbox.exceptions.ApiError as e:
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
