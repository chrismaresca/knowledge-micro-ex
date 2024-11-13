# Typing
from typing import Any, Optional, List
from fastapi import UploadFile, HTTPException
from abc import ABC, abstractmethod

import re

# Boto3
import boto3
from botocore.exceptions import ClientError


# Pydantic
from pydantic import BaseModel

# TempFile and OS
import tempfile
import os

# Import Exceptions
from app import exceptions


# ABC Models
# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------------------------------------------- #


class RemoteFileResponse(BaseModel):
    success: bool
    message: str
    file_key: Optional[str] = None
    file_name: Optional[str] = None


class RemoteFileService(ABC):
    @abstractmethod
    async def upload_file(
        self,
        file: UploadFile,
        dir_path: Optional[str] = None,
        file_name: Optional[str] = None,
        file_key: Optional[str] = None,
        tags: Optional[dict] = None
    ) -> RemoteFileResponse:
        pass

    @abstractmethod
    async def move_file(self, old_key: str, new_dir: str, file_name: str) -> RemoteFileResponse:
        pass

    @abstractmethod
    async def delete_file(self, file_key: str) -> RemoteFileResponse:
        pass

    @abstractmethod
    async def delete_directory(self, dir_key: str) -> RemoteFileResponse:
        pass


# S3 Models
# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------------------------------------------- #


class S3Response(RemoteFileResponse):
    pass

# S3 Utility Functions
# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------------------------------------------- #


def construct_file_key(dir_path: Optional[str], file_name: Optional[str], s3_file_key: Optional[str]) -> str:
    """
    Constructs a file key for S3 uploads based on directory path, file name, or a direct file key.
    """

    if s3_file_key and (dir_path or file_name):
        raise ValueError("Provide either 's3_file_key' or 'dir_path' and 'file_name', not both.")
    if not s3_file_key:
        if not dir_path or not file_name:
            raise ValueError("If 's3_file_key' is not provided, both 'dir_path' and 'file_name' must be supplied.")
        if not dir_path.endswith('/'):
            dir_path += '/'
        s3_file_key = f"{dir_path}{file_name}"
    return s3_file_key


async def upload_to_s3(s3_client: boto3.Session.resource, bucket_name: str, file: UploadFile, s3_file_key: str, tags: Optional[dict] = None):
    """
    Uploads a file from FastAPI's UploadFile to an S3 bucket.
    """
    # Read the content of the UploadFile
    byte_content = await file.read()

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(byte_content)
            tmp_file_path = tmp_file.name

       # Upload the temporary file to the S3 bucket
        extra_args = {'Tagging': '&'.join(f"{key}={value}" for key, value in tags.items())} if tags else {}
        s3_client.Bucket(bucket_name).upload_file(tmp_file_path, s3_file_key, ExtraArgs=extra_args)
    finally:
        # Clean up the temporary file
        if 'tmp_file_path' in locals():
            os.remove(tmp_file_path)


class S3Service(RemoteFileService):

    def __init__(self, s3_client_connection: boto3.resource, bucket_name: str = 'workmaitblogimages'):
        """
        Initialize S3 Handler with a client connection and a default bucket name.
        """
        self.s3_client = s3_client_connection
        self.bucket_name = bucket_name

    async def upload_file(self,
                          file: UploadFile,
                          dir_path: Optional[str] = None,
                          file_name: Optional[str] = None,
                          file_key: Optional[str] = None,
                          tags: Optional[dict] = None) -> S3Response:
        """
        Uploads a file or bytes to the configured S3 bucket.
        """

        # Construct the file key
        file_key = construct_file_key(dir_path, file_name, file_key)

        try:
            await upload_to_s3(self.s3_client, self.bucket_name, file, file_key, tags)
            return S3Response(success=True, message="File uploaded successfully.", file_key=file_key, file_name=file_name)
        except ClientError as e:
            return S3Response(success=False, message=f"Failed to upload file: {str(e)}")
        except Exception as e:
            return S3Response(success=False, message=f"Failed to upload file: {str(e)}")

    async def delete_file(self, file_key: str) -> S3Response:
        """
        Deletes a single file from the S3 bucket.
        """
        try:
            obj = self.s3_client.Object(self.bucket_name, file_key)
            await obj.delete()
            return S3Response(success=True, message="File deleted successfully.", file_key=file_key)
        except ClientError as e:
            return S3Response(success=False, message=f"Failed to delete file: {str(e)}", file_key=file_key)
        except Exception as e:
            return S3Response(success=False, message=f"Failed to delete file: {str(e)}", file_key=file_key)

    async def delete_directory(self, dir_key: str) -> S3Response:
        """
        Deletes a directory (all files within a directory) from the S3 bucket.
        """
        try:
            # List all objects within the directory
            objects_to_delete = self.s3_client.meta.client.list_objects_v2(Bucket=self.bucket_name, Prefix=dir_key)
            if 'Contents' in objects_to_delete:
                delete_responses = []
                for obj in objects_to_delete['Contents']:
                    obj_key = obj['Key']
                    response = await self.delete_file(obj_key)
                    delete_responses.append(response)
                success = all(resp.success for resp in delete_responses)
                message = "All objects deleted successfully." if success else "Some objects could not be deleted."
                return S3Response(success=success, message=message, file_key=dir_key)
            else:
                return S3Response(success=False, message="Directory not found.", file_key=dir_key)
        except ClientError as e:
            return S3Response(success=False, message=f"Failed to delete directory: {str(e)}", file_key=dir_key)
        except Exception as e:
            return S3Response(success=False, message=f"Failed to delete directory: {str(e)}", file_key=dir_key)

    async def move_file(self, old_key: str, new_dir: str, file_name: str) -> S3Response:
        """
        Moves a file from one key to another within the S3 bucket.
        """
        new_key = construct_file_key(new_dir, file_name)

        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': old_key}
            self.s3_client.Object(self.bucket_name, new_key).copy_from(CopySource=copy_source)
            await self.delete_file(old_key)
            return S3Response(success=True, message="File moved successfully.", file_key=new_key)
        except ClientError as e:
            return S3Response(success=False, message=f"Failed to move file: {str(e)}", file_key=new_key)
        except Exception as e:
            return S3Response(success=False, message=f"Failed to move file: {str(e)}", file_key=new_key)
