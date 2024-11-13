# Typing Imports
from typing import Optional, List

# Pydantic
from pydantic import BaseModel, Field
from fastapi import UploadFile, File


# Resource Document
from app.models import ResourceDocument, Visibility


# File Upload Schemas
# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------------------------------------------- #


class FileUploadError(BaseModel):
    filename: str
    error_message: Optional[str]


class FileUploadSuccess(BaseModel):
    filename: str
    resource: ResourceDocument


class UploadSummary(BaseModel):
    successes: List[FileUploadSuccess]
    errors: List[FileUploadError]


# KnowledgeBase Request Schemas
# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------------------------------------------- #

class CreateKnowledgebaseRequest(BaseModel):
    name: str = Field(..., description="The name of the knowledgebase")
    files: List[UploadFile] = Field(..., description="List of files to be uploaded")
    visibility: Visibility = Field(default=Visibility.PRIVATE, description="Visibility of the knowledge base, can be 'public' or 'private'")


class AddResourcesRequest(BaseModel):
    files: List[UploadFile] = Field(..., description="List of files to be added")


class DeleteResourcesRequest(BaseModel):
    resource_ids: List[str] = Field(..., description="List of resource IDs to be deleted")


class ShareKnowledgebaseRequest(BaseModel):
    resource_ids: List[str] = Field(..., description="List of resource IDs to be shared")
    user_ids: List[str] = Field(..., description="List of user IDs to share the resources with")


class RenameKnowledgebaseRequest(BaseModel):
    new_name: str = Field(..., description="The new name of the knowledgebase")


class RenameFileRequest(BaseModel):
    file_id: str = Field(..., description="The ID of the file to be renamed")
    new_name: str = Field(..., description="The new name of the file")

# Redis Event Payloads
# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------------------------------------------- #


class ToLlamaDocsEventPayload(BaseModel):
    remote_file_keys: List[str]
