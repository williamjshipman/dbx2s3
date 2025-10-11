"""Abstract storage interface."""

from abc import ABC, abstractmethod
from typing import Optional


class Storage(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def upload_file(self, key: str, data: bytes, metadata: Optional[dict] = None) -> None:
        """Upload a file to storage.
        
        Args:
            key: Object key/path
            data: File content
            metadata: Optional metadata to attach to the object
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
