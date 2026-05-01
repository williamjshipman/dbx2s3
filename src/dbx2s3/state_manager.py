"""State management for incremental backups.

This module provides atomic state persistence for incremental backup operations.
State files are written atomically using temporary files and atomic rename operations
to prevent corruption from interrupted writes or system crashes.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional
from datetime import UTC, datetime


logger = logging.getLogger(__name__)


class StateManager:
    """Manages backup state for incremental backups."""
    
    def __init__(self, state_file: str):
        """Initialize state manager.
        
        Args:
            state_file: Path to state file
        """
        self.state_file = Path(state_file)
        self.state: Dict[str, dict] = {}
        self._load_state()
    
    def _load_state(self) -> None:
        """Load state from file with corruption recovery.

        If the state file is corrupted (invalid JSON), it will be backed up
        with a .corrupt suffix and a fresh state will be initialized.
        """
        if not self.state_file.exists():
            logger.info(
                "state_init_fresh",
                extra={"state_file": str(self.state_file)}
            )
            self.state = {}
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                loaded_state = json.load(f)

            # Validate state structure
            if not isinstance(loaded_state, dict):
                raise ValueError("State file must contain a JSON object")

            self.state = loaded_state
            logger.info(
                "state_loaded",
                extra={
                    "state_file": str(self.state_file),
                    "file_count": len(self.state)
                }
            )

        except json.JSONDecodeError as e:
            # Backup corrupted file
            backup_path = self.state_file.with_suffix('.corrupt.json')
            try:
                self.state_file.rename(backup_path)
                logger.warning(
                    "state_corrupted_backed_up",
                    extra={
                        "state_file": str(self.state_file),
                        "backup_path": str(backup_path),
                        "error": str(e)
                    }
                )
            except OSError as rename_error:
                logger.error(
                    "state_backup_failed",
                    extra={"error": str(rename_error)},
                    exc_info=True
                )

            self.state = {}

        except Exception as e:
            logger.error(
                "state_load_failed",
                extra={
                    "state_file": str(self.state_file),
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            self.state = {}
    
    def _save_state(self) -> None:
        """Save state to file atomically.

        Uses atomic write operations to prevent state corruption:
        1. Write to temporary file in same directory
        2. Flush and fsync to ensure data is on disk
        3. Atomically rename temp file to target (os.replace)
        4. Set restrictive permissions (owner read/write only)

        This ensures that crashes during write never leave a partially
        written or corrupted state file.
        """
        try:
            # Ensure parent directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # Create temporary file in same directory for atomic rename
            fd, temp_path = tempfile.mkstemp(
                dir=self.state_file.parent,
                prefix=f".{self.state_file.stem}_",
                suffix=".tmp"
            )

            try:
                # Write state to temp file with explicit flush and fsync
                with os.fdopen(fd, 'w') as f:
                    json.dump(self.state, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())

                # Atomically replace target file (works on all platforms)
                os.replace(temp_path, self.state_file)

                # Set restrictive permissions (owner read/write only)
                if hasattr(os, 'chmod'):
                    os.chmod(self.state_file, 0o600)

                logger.debug(
                    "state_saved",
                    extra={
                        "state_file": str(self.state_file),
                        "file_count": len(self.state),
                        "operation": "atomic_write"
                    }
                )

            except Exception:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise

        except OSError as e:
            logger.error(
                "state_save_failed",
                extra={
                    "state_file": str(self.state_file),
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise
    
    def should_backup_file(self, path: str, rev: str, size: int) -> bool:
        """Check if a file should be backed up.
        
        Args:
            path: File path
            rev: File revision
            size: File size
            
        Returns:
            True if file should be backed up
        """
        if path not in self.state:
            logger.debug(f"{path} not in state, needs backup")
            return True
        
        file_state = self.state[path]
        if file_state.get("rev") != rev:
            logger.debug(f"{path} revision changed, needs backup")
            return True
        
        if file_state.get("size") != size:
            logger.debug(f"{path} size changed, needs backup")
            return True
        
        logger.debug(f"{path} unchanged, skipping")
        return False
    
    def mark_file_backed_up(
        self,
        path: str,
        rev: str,
        size: int,
        content_hash: Optional[str] = None
    ) -> None:
        """Mark a file as backed up.
        
        Args:
            path: File path
            rev: File revision
            size: File size
            content_hash: Optional content hash
        """
        self.state[path] = {
            "rev": rev,
            "size": size,
            "content_hash": content_hash,
            "backed_up_at": datetime.now(UTC).isoformat(),
        }
        self._save_state()
    
    def get_file_state(self, path: str) -> Optional[dict]:
        """Get state for a file.
        
        Args:
            path: File path
            
        Returns:
            State dictionary or None
        """
        return self.state.get(path)
    
    def remove_file_state(self, path: str) -> None:
        """Remove state for a file.
        
        Args:
            path: File path
        """
        if path in self.state:
            del self.state[path]
            self._save_state()
