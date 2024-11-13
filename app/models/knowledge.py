# Typing Imports
from typing import Optional, List

# Datetime
from datetime import datetime, timezone

# Pydantic
from pydantic import BaseModel, Field, field_validator, HttpUrl
from pydantic_core import PydanticCustomError

# Pymongo and Beanie
from pymongo import (IndexModel, DESCENDING as pyDESCENDING, ASCENDING as pyASCENDING)

from beanie import Document
from beanie.odm.fields import PydanticObjectId

from enum import Enum


class Visibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


# ------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------- #
#  KnowledgeBaseDocument

class KnowledgeBaseDocument(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    name: str
    user_id: PydanticObjectId

    visibility: Visibility = Field(default=Visibility.PRIVATE, description="Visibility of the knowledge base, can be 'public' or 'private'")

    # remote directory
    remote_dir: Optional[str] = None

    # Resources payload and Resources
    resources: Optional[List["ResourceMetadata"]] = Field(default_factory=list, description="Where resource metadata is stored.")

    # Date info
    date_created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    date_last_modified: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_bases"
        is_root = True
        indexes = [
            IndexModel("user_id", unique=False),
            IndexModel([("date_last_modified", pyDESCENDING)])
        ]


# ------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------- #
#  ResourceDocument

class ResourceMetadata(BaseModel):
    resource_id: PydanticObjectId
    name: str
    remote_file_key: Optional[str] = None
    preview_image_url: Optional[HttpUrl] = None
    resource_type: Optional[str] = None
    in_vector_store: bool = False


class ResourceDocument(Document):
    resource_id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    name: str
    user_id: PydanticObjectId

    visibility: Visibility = Field(default=Visibility.PRIVATE, description="Visibility of the knowledge base, can be 'public' or 'private'")

    # remote file key info
    remote_file_key: Optional[str] = Field(default=None, description="The remote file key of this resource")

    # KB Info
    knowledgebase_id: Optional[PydanticObjectId] = Field(default=None)
    knowledgebase_name: Optional[str] = Field(default=None)

    # Vector Store
    in_vector_store: bool = Field(default=False, description="True if this resource is in a vector store. False if not.")

    # Preview image URL
    preview_image_url: Optional[HttpUrl] = None
    resource_type: Optional[str] = None
    num_docs: Optional[int] = None

    # Date info
    date_created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    date_last_modified: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "resources"
        is_root = True
        indexes = [
            IndexModel("user_id", unique=False),
            IndexModel([("knowledgebase_id", pyASCENDING)],
                       name="knowledgebase_id_index"),
            IndexModel([("date_last_modified", pyDESCENDING)])
        ]

    def to_metadata(self) -> ResourceMetadata:
        """
        Function to return the resource metadata quickly.
        """
        return ResourceMetadata(resource_id=str(self.resource_id),
                                name=self.name,
                                remote_file_key=self.remote_file_key,
                                preview_image_url=self.preview_image_url if self.preview_image_url else None,
                                resource_type=self.resource_type if self.resource_type else None,
                                in_vector_store=self.in_vector_store if self.in_vector_store else False
                                )
