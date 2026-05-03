"""Main backup logic."""

import logging
from typing import Optional

from .dropbox_client import DropboxClient
from .storage import Storage
from .state_manager import StateManager


logger = logging.getLogger(__name__)


class BackupManager:
    """Manages the backup process."""
    
    def __init__(
        self,
        dropbox_client: DropboxClient,
        storage: Storage,
        state_manager: StateManager,
    ):
        """Initialize backup manager.
        
        Args:
            dropbox_client: Dropbox client instance
            storage: Storage backend instance
            state_manager: State manager instance
        """
        self.dropbox = dropbox_client
        self.storage = storage
        self.state = state_manager
    
    def backup(self, path: str = "", resume: bool = True) -> dict:
        """Perform backup of Dropbox to storage.
        
        Args:
            path: Starting path in Dropbox (empty for root)
            resume: Whether to resume from previous state
            
        Returns:
            Dictionary with backup statistics
        """
        logger.info("Starting backup...")
        logger.info(f"Resume mode: {resume}")

        stats = {
            "total_files": 0,
            "backed_up": 0,
            "skipped": 0,
            "errors": 0,
        }

        try:
            for file_metadata in self.dropbox.list_all_files(path):
                stats["total_files"] += 1
                file_path = file_metadata.path_display
                
                try:
                    # Check if we should backup this file
                    if resume and not self.state.should_backup_file(
                        file_path,
                        file_metadata.rev,
                        file_metadata.size
                    ):
                        stats["skipped"] += 1
                        continue
                    
                    # Download and upload file using streaming for memory efficiency
                    logger.info(f"Backing up: {file_path}")

                    storage_key = self._get_storage_key(file_path)

                    # Use streaming download for memory-efficient transfer
                    with self.dropbox.download_file_stream(file_path) as (download_metadata, chunks):
                        storage_metadata = {
                            "dropbox_path": file_path,
                            "dropbox_rev": download_metadata.rev,
                            "dropbox_size": str(download_metadata.size),
                            "dropbox_modified": download_metadata.server_modified.isoformat(),
                        }

                        # Upload using streaming - storage backends handle chunk iteration
                        self.storage.upload_file(storage_key, chunks, storage_metadata)

                        # Record the metadata for the file version that was actually uploaded.
                        self.state.mark_file_backed_up(
                            file_path,
                            download_metadata.rev,
                            download_metadata.size,
                            getattr(download_metadata, "content_hash", None),
                        )
                    
                    stats["backed_up"] += 1
                    logger.info(
                        f"Progress: {stats['backed_up']}/{stats['total_files']} "
                        f"files backed up, {stats['skipped']} skipped"
                    )
                    
                except Exception as e:
                    logger.error(f"Error backing up {file_path}: {e}")
                    stats["errors"] += 1
                    continue
            
            logger.info("Backup completed!")
            logger.info(
                f"Total: {stats['total_files']}, "
                f"Backed up: {stats['backed_up']}, "
                f"Skipped: {stats['skipped']}, "
                f"Errors: {stats['errors']}"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def _get_storage_key(self, dropbox_path: str) -> str:
        """Convert Dropbox path to storage key.
        
        Args:
            dropbox_path: Path in Dropbox
            
        Returns:
            Storage key
        """
        # Remove leading slash and use path as-is
        key = dropbox_path.lstrip("/")
        return key if key else "root"
