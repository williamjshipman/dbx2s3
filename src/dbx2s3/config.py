"""Configuration management for dbx2s3."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration for the backup tool."""
    
    dropbox_token: str
    storage_type: str
    s3_endpoint: Optional[str]
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str
    s3_region: Optional[str]
    azure_connection_string: Optional[str]
    azure_container: Optional[str]
    state_file: str
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()
        
        dropbox_token = os.getenv("DROPBOX_TOKEN")
        if not dropbox_token:
            raise ValueError("DROPBOX_TOKEN environment variable is required")
        
        storage_type = os.getenv("STORAGE_TYPE", "s3").lower()
        
        if storage_type in ["s3", "aws"]:
            s3_access_key = os.getenv("S3_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID")
            s3_secret_key = os.getenv("S3_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
            s3_bucket = os.getenv("S3_BUCKET")
            
            if not all([s3_access_key, s3_secret_key, s3_bucket]):
                raise ValueError(
                    "S3_ACCESS_KEY, S3_SECRET_KEY, and S3_BUCKET are required for S3 storage"
                )
            
            return cls(
                dropbox_token=dropbox_token,
                storage_type=storage_type,
                s3_endpoint=os.getenv("S3_ENDPOINT"),
                s3_access_key=s3_access_key,
                s3_secret_key=s3_secret_key,
                s3_bucket=s3_bucket,
                s3_region=os.getenv("S3_REGION", "us-east-1"),
                azure_connection_string=None,
                azure_container=None,
                state_file=os.getenv("STATE_FILE", ".dbx2s3_state.json"),
            )
        
        elif storage_type == "azure":
            azure_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            azure_container = os.getenv("AZURE_CONTAINER")
            
            if not all([azure_connection_string, azure_container]):
                raise ValueError(
                    "AZURE_STORAGE_CONNECTION_STRING and AZURE_CONTAINER are required for Azure storage"
                )
            
            return cls(
                dropbox_token=dropbox_token,
                storage_type=storage_type,
                s3_endpoint=None,
                s3_access_key="",
                s3_secret_key="",
                s3_bucket="",
                s3_region=None,
                azure_connection_string=azure_connection_string,
                azure_container=azure_container,
                state_file=os.getenv("STATE_FILE", ".dbx2s3_state.json"),
            )
        
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
