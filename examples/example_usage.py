#!/usr/bin/env python3
"""
Example demonstrating dbx2s3 usage.

This script shows how to use dbx2s3 programmatically instead of via CLI.
"""

import os
import sys
import logging

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dbx2s3.config import Config
from dbx2s3.dropbox_client import DropboxClient
from dbx2s3.s3_storage import S3Storage, AzureBlobStorage
from dbx2s3.state_manager import StateManager
from dbx2s3.backup import BackupManager


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def example_s3_backup():
    """Example: Backup Dropbox to Amazon S3."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration from environment
    # Make sure to set these environment variables:
    # - DROPBOX_TOKEN
    # - STORAGE_TYPE=s3
    # - S3_BUCKET
    # - S3_ACCESS_KEY
    # - S3_SECRET_KEY
    # - S3_REGION (optional)
    
    try:
        config = Config.from_env()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Please set the required environment variables.")
        return
    
    # Initialize clients
    dropbox_client = DropboxClient(config.dropbox_token)
    storage = S3Storage(
        bucket=config.s3_bucket,
        access_key=config.s3_access_key,
        secret_key=config.s3_secret_key,
        endpoint=config.s3_endpoint,
        region=config.s3_region,
    )
    state_manager = StateManager(config.state_file)
    
    # Run backup
    backup_manager = BackupManager(dropbox_client, storage, state_manager)
    stats = backup_manager.backup(path="", resume=True)
    
    logger.info(f"Backup complete! Stats: {stats}")


def example_azure_backup():
    """Example: Backup Dropbox to Azure Blob Storage."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration from environment
    # Make sure to set these environment variables:
    # - DROPBOX_TOKEN
    # - STORAGE_TYPE=azure
    # - AZURE_STORAGE_CONNECTION_STRING
    # - AZURE_CONTAINER
    
    try:
        config = Config.from_env()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Please set the required environment variables.")
        return
    
    # Initialize clients
    dropbox_client = DropboxClient(config.dropbox_token)
    storage = AzureBlobStorage(
        connection_string=config.azure_connection_string,
        container=config.azure_container,
    )
    state_manager = StateManager(config.state_file)
    
    # Run backup
    backup_manager = BackupManager(dropbox_client, storage, state_manager)
    stats = backup_manager.backup(path="", resume=True)
    
    logger.info(f"Backup complete! Stats: {stats}")


def example_custom_s3_backup():
    """Example: Backup Dropbox to custom S3-compatible storage (e.g., MinIO)."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # For custom S3-compatible storage, set:
    # - DROPBOX_TOKEN
    # - STORAGE_TYPE=s3
    # - S3_ENDPOINT=https://your-minio-server.com
    # - S3_BUCKET
    # - S3_ACCESS_KEY
    # - S3_SECRET_KEY
    # - S3_REGION (optional)
    
    try:
        config = Config.from_env()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Please set the required environment variables.")
        return
    
    if not config.s3_endpoint:
        logger.error("S3_ENDPOINT must be set for custom S3-compatible storage")
        return
    
    # Initialize clients
    dropbox_client = DropboxClient(config.dropbox_token)
    storage = S3Storage(
        bucket=config.s3_bucket,
        access_key=config.s3_access_key,
        secret_key=config.s3_secret_key,
        endpoint=config.s3_endpoint,
        region=config.s3_region or "us-east-1",
    )
    state_manager = StateManager(config.state_file)
    
    # Run backup
    backup_manager = BackupManager(dropbox_client, storage, state_manager)
    stats = backup_manager.backup(path="", resume=True)
    
    logger.info(f"Backup complete! Stats: {stats}")


if __name__ == "__main__":
    # Run based on STORAGE_TYPE environment variable
    storage_type = os.getenv("STORAGE_TYPE", "s3").lower()
    
    if storage_type in ["s3", "aws"]:
        if os.getenv("S3_ENDPOINT"):
            print("Running custom S3-compatible storage backup example...")
            example_custom_s3_backup()
        else:
            print("Running Amazon S3 backup example...")
            example_s3_backup()
    elif storage_type == "azure":
        print("Running Azure Blob Storage backup example...")
        example_azure_backup()
    else:
        print(f"Unknown storage type: {storage_type}")
        print("Set STORAGE_TYPE to 's3', 'aws', or 'azure'")
