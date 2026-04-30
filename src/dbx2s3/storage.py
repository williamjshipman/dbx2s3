"""Abstract storage interface.

This module defines the abstract interface for storage backends with support
for both traditional byte-based uploads and streaming uploads for large files.

Streaming uploads allow memory-efficient transfer of large files by processing
them in chunks rather than loading entire files into memory.
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Iterable, Optional, Union


# Type alias for upload sources: raw bytes, file-like objects, or iterables of chunks
UploadSource = Union[bytes, BinaryIO, Iterable[bytes]]


class Storage(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def upload_file(self, key: str, data: UploadSource, metadata: Optional[dict] = None) -> None:
        """Upload a file to storage.

        Supports multiple data source types for flexibility:
        - bytes: Traditional in-memory upload (for small files)
        - BinaryIO: File-like object with read() method
        - Iterable[bytes]: Generator or iterator yielding chunks

        Args:
            key: Object key/path
            data: File content as bytes, file-like object, or byte chunks
            metadata: Optional metadata to attach to the object

        Note:
            For large files (>100MB), prefer using file-like objects or
            iterables to avoid loading entire file into memory.
        """
        pass
    
    @abstractmethod
    def file_exists(self, key: str) -> bool:
        """Check if a file exists in storage.
        
        Args:
            key: Object key/path
            
        Returns:
            True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_file_metadata(self, key: str) -> Optional[dict]:
        """Get metadata for a file.
        
        Args:
            key: Object key/path
            
        Returns:
            Metadata dictionary or None if file doesn't exist
        """
        pass
