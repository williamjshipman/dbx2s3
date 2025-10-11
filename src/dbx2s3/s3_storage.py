"""S3-compatible storage implementation."""

import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from azure.storage.blob import BlobServiceClient

from .storage import Storage


logger = logging.getLogger(__name__)


class S3Storage(Storage):
    """S3-compatible storage backend."""
    
    def __init__(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint: Optional[str] = None,
        region: str = "us-east-1",
    ):
        """Initialize S3 storage.
        
        Args:
            bucket: S3 bucket name
            access_key: AWS access key ID
            secret_key: AWS secret access key
            endpoint: Optional custom endpoint URL for S3-compatible services
            region: AWS region
        """
        self.bucket = bucket
        
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        
        if endpoint:
            self.s3 = session.client("s3", endpoint_url=endpoint)
        else:
            self.s3 = session.client("s3")
        
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.s3.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket {self.bucket} exists")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                logger.info(f"Creating bucket {self.bucket}")
                self.s3.create_bucket(Bucket=self.bucket)
            else:
                raise
    
    def upload_file(self, key: str, data: bytes, metadata: Optional[dict] = None) -> None:
        """Upload a file to S3.
        
        Args:
            key: Object key
            data: File content
            metadata: Optional metadata
        """
        try:
            extra_args = {}
            if metadata:
                extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}
            
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                **extra_args
            )
            logger.info(f"Uploaded {key} to S3")
        except ClientError as e:
            logger.error(f"Error uploading {key}: {e}")
            raise
    
    def file_exists(self, key: str) -> bool:
        """Check if file exists in S3.
        
        Args:
            key: Object key
            
        Returns:
            True if file exists
        """
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                return False
            raise
    
    def get_file_metadata(self, key: str) -> Optional[dict]:
        """Get metadata for a file.
        
        Args:
            key: Object key
            
        Returns:
            Metadata dictionary or None
        """
        try:
            response = self.s3.head_object(Bucket=self.bucket, Key=key)
            return response.get("Metadata", {})
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                return None
            raise


class AzureBlobStorage(Storage):
    """Azure Blob Storage backend."""
    
    def __init__(self, connection_string: str, container: str):
        """Initialize Azure Blob Storage.
        
        Args:
            connection_string: Azure storage connection string
            container: Container name
        """
        self.container = container
        self.blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        self.container_client = self.blob_service_client.get_container_client(container)
        
        self._ensure_container_exists()
    
    def _ensure_container_exists(self) -> None:
        """Create container if it doesn't exist."""
        try:
            self.container_client.get_container_properties()
            logger.info(f"Container {self.container} exists")
        except Exception:
            logger.info(f"Creating container {self.container}")
            self.container_client.create_container()
    
    def upload_file(self, key: str, data: bytes, metadata: Optional[dict] = None) -> None:
        """Upload a file to Azure Blob Storage.
        
        Args:
            key: Blob name
            data: File content
            metadata: Optional metadata
        """
        try:
            blob_client = self.container_client.get_blob_client(key)
            blob_client.upload_blob(
                data,
                overwrite=True,
                metadata=metadata if metadata else None
            )
            logger.info(f"Uploaded {key} to Azure Blob Storage")
        except Exception as e:
            logger.error(f"Error uploading {key}: {e}")
            raise
    
    def file_exists(self, key: str) -> bool:
        """Check if blob exists in Azure.
        
        Args:
            key: Blob name
            
        Returns:
            True if blob exists
        """
        try:
            blob_client = self.container_client.get_blob_client(key)
            blob_client.get_blob_properties()
            return True
        except Exception:
            return False
    
    def get_file_metadata(self, key: str) -> Optional[dict]:
        """Get metadata for a blob.
        
        Args:
            key: Blob name
            
        Returns:
            Metadata dictionary or None
        """
        try:
            blob_client = self.container_client.get_blob_client(key)
            properties = blob_client.get_blob_properties()
            return properties.metadata
        except Exception:
            return None
