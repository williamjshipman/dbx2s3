"""State management for incremental backups."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


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
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    self.state = json.load(f)
                logger.info(f"Loaded state from {self.state_file}")
                logger.info(f"State contains {len(self.state)} files")
            except Exception as e:
                logger.warning(f"Error loading state file: {e}")
                self.state = {}
        else:
            logger.info("No existing state file found, starting fresh")
            self.state = {}
    
    def _save_state(self) -> None:
        """Save state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
            logger.debug(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
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
            "backed_up_at": datetime.utcnow().isoformat(),
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
