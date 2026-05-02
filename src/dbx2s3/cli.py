"""Command-line interface for dbx2s3."""

import argparse
import logging
import sys

from .config import Config
from .dropbox_client import DropboxClient
from .s3_storage import S3Storage, AzureBlobStorage
from .state_manager import StateManager
from .backup import BackupManager


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Backup Dropbox to S3-compatible storage"
    )
    parser.add_argument(
        "--path",
        default="",
        help="Dropbox path to backup (default: root)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Disable resume functionality (backup all files)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = Config.from_env()
        
        # Initialize Dropbox client
        logger.info("Initializing Dropbox client...")
        dropbox_client = DropboxClient(
            config.dropbox_token,
            retry_max_attempts=config.dropbox_retry_max_attempts,
            retry_base_delay=config.dropbox_retry_base_delay,
        )
        
        # Initialize storage backend
        logger.info(f"Initializing {config.storage_type} storage...")
        if config.storage_type in ["s3", "aws"]:
            storage = S3Storage(
                bucket=config.s3_bucket,
                access_key=config.s3_access_key,
                secret_key=config.s3_secret_key,
                endpoint=config.s3_endpoint,
                region=config.s3_region or "us-east-1",
            )
        elif config.storage_type == "azure":
            storage = AzureBlobStorage(
                connection_string=config.azure_connection_string,
                container=config.azure_container,
            )
        else:
            logger.error(f"Unsupported storage type: {config.storage_type}")
            return 1
        
        # Initialize state manager
        logger.info("Initializing state manager...")
        state_manager = StateManager(config.state_file)
        
        # Initialize backup manager and run backup
        backup_manager = BackupManager(dropbox_client, storage, state_manager)
        stats = backup_manager.backup(
            path=args.path,
            resume=not args.no_resume,
        )
        
        if stats["errors"] > 0:
            logger.warning(f"Backup completed with {stats['errors']} errors")
            return 1
        
        logger.info("Backup completed successfully!")
        return 0
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Backup interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
