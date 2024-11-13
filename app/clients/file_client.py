# Boto3
import boto3
import s3fs

# Import configuration
from app.config import workmait_config


from abc import ABC, abstractmethod


class RemoteFileServiceClient(ABC):
    """Abstract base class for remote file service clients."""

    @abstractmethod
    def get_resource(self):
        pass

    @abstractmethod
    def get_filesystem(self):
        pass


class S3Client(RemoteFileServiceClient):
    """Manages S3 connections, providing both boto3 resource and s3fs file system."""
    _resource_instance = None
    _filesystem_instance = None

    @classmethod
    def initialize(cls):
        """Initialize the S3 client connections."""
        # Initialize boto3 resource
        if cls._resource_instance is None:
            cls._resource_instance = boto3.resource(
                's3',
                aws_access_key_id=workmait_config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=workmait_config.AWS_SECRET_ACCESS_KEY
            )

        # Initialize s3fs filesystem
        if cls._filesystem_instance is None:
            cls._filesystem_instance = s3fs.S3FileSystem(
                key=workmait_config.AWS_ACCESS_KEY_ID,
                secret=workmait_config.AWS_SECRET_ACCESS_KEY
            )

    @classmethod
    def get_resource(cls):
        """Return the boto3 resource instance, initializing if not already done."""
        if cls._resource_instance is None:
            cls.initialize()  # Ensure it is initialized
        return cls._resource_instance

    @classmethod
    def get_filesystem(cls):
        """Return the s3fs filesystem instance, initializing if not already done."""
        if cls._filesystem_instance is None:
            cls.initialize()  # Ensure it is initialized
        return cls._filesystem_instance
