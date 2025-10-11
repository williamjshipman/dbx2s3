"""Basic tests for dbx2s3."""

import json
import tempfile
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dbx2s3.state_manager import StateManager


def test_state_manager():
    """Test state manager functionality."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        state_file = f.name
    
    try:
        # Create state manager
        manager = StateManager(state_file)
        
        # Test initial state
        assert manager.should_backup_file("/test.txt", "rev1", 100) is True
        
        # Mark file as backed up
        manager.mark_file_backed_up("/test.txt", "rev1", 100)
        
        # Should not need backup anymore
        assert manager.should_backup_file("/test.txt", "rev1", 100) is False
        
        # Should need backup if revision changes
        assert manager.should_backup_file("/test.txt", "rev2", 100) is True
        
        # Should need backup if size changes
        assert manager.should_backup_file("/test.txt", "rev1", 200) is True
        
        # Get state
        state = manager.get_file_state("/test.txt")
        assert state is not None
        assert state["rev"] == "rev1"
        assert state["size"] == 100
        
        # Test persistence
        manager2 = StateManager(state_file)
        assert manager2.should_backup_file("/test.txt", "rev1", 100) is False
        
        print("✓ State manager tests passed")
        
    finally:
        # Clean up
        if os.path.exists(state_file):
            os.unlink(state_file)


def test_config_validation():
    """Test configuration validation."""
    # Test missing required env var
    os.environ.pop("DROPBOX_TOKEN", None)
    
    try:
        from dbx2s3.config import Config
        Config.from_env()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "DROPBOX_TOKEN" in str(e)
        print("✓ Config validation tests passed")


if __name__ == "__main__":
    print("Running tests...")
    test_state_manager()
    test_config_validation()
    print("\nAll tests passed!")
