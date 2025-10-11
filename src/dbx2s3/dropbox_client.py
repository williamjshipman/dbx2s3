"""Dropbox client for enumerating and downloading files."""

import logging
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
        """Download a file from Dropbox.
        
        Args:
            path: Path to the file in Dropbox
            
        Returns:
            Tuple of (file content as bytes, file metadata)
        """
        try:
            metadata, response = self.dbx.files_download(path)
            content = response.content
            logger.debug(f"Downloaded {path}: {len(content)} bytes")
            return content, metadata
        except dropbox.exceptions.ApiError as e:
            logger.error(f"Error downloading {path}: {e}")
            raise
    
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
