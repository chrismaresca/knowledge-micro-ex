from typing import List, Dict, Union, Any, Tuple, Optional, Union
import re

# FastAPI
from fastapi import UploadFile, HTTPException, File, status

# Beanie
from beanie import PydanticObjectId
import validators


# Import models
from app.models import ResourceDocument, KnowledgeBaseDocument, Visibility

# Import Exceptions
from app import exceptions

# Import Services
from app.services.file_service import RemoteFileService
from app.services.knowledge_service import KnowledgeBaseService, UploadSummary


# Utility Functions
# --------------------------------------------------------------------------------------------------------------------------------------------------- #


def construct_directory_key(directories: list[str], max_depth: int = 2) -> str:
    """
    Constructs and validates a directory path from a list of directory names.
    """
    if not directories or len(directories) > max_depth:
        raise exceptions.InvalidPathError(f"Must provide between 1 and {max_depth} directory names.")

    invalid_directories = [directory for directory in directories if not validators.slug(directory)]
    if invalid_directories:
        raise exceptions.InvalidPathError(f"Invalid directory names: {', '.join(invalid_directories)}")

    return None


class AppService:
    """
    Knowledge Base Service Handler
    """

    def __init__(self, kb_service: KnowledgeBaseService):
        self.kb_service = kb_service

    def validate_name(self, name: str) -> None:
        """
        Helper to validate a name.
        """
        name = name.strip()
        if '  ' in name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name: contains multiple consecutive spaces.")
        name = name.replace(' ', '-')
        if not validators.slug(name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name: contains special characters or improper use of hyphens.")

    def check_permission(self, entity: Union[ResourceDocument, KnowledgeBaseDocument], user_id: Optional[str]):
        if entity.visibility != Visibility.PRIVATE:
            return
        if entity.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to modify this entity.")

    async def get_knowledgebase(self, kb_id: str) -> KnowledgeBaseDocument:
        """
        Get KB by id with HTTP Exception Handling.
        """
        try:
            return await self.kb_service.get_knowledgebase_by_id(kb_id)
        except exceptions.KnowledgeBaseNotFound:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Knowledge base {kb_id} not found")
        except exceptions.KBException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")

    async def get_resource(self, resource_id: str) -> ResourceDocument:
        """
        Get Resource by id with HTTP Exception Handling.
        """
        try:
            return await self.kb_service.get_resource_by_id(resource_id)
        except exceptions.ResourceNotFound:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource {resource_id} not found")
        except exceptions.ResourceException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")

    async def create_knowledgebase(self, name: str, visibility: Visibility = Visibility.PRIVATE, user_id: Optional[str] = None, files: Optional[List[UploadFile]] = File(...)) -> UploadSummary:
        """
        Create a knowledgebase from file uploads.
        """
        self.validate_name(name)
        knowledgebase_id = PydanticObjectId()
        remote_dir = construct_directory_key(directories=[str(user_id), str(knowledgebase_id)] if user_id else [str(knowledgebase_id)])

        kb_create_dict = {
            'id': knowledgebase_id,
            'name': name,
            'remote_dir': remote_dir,
            'visibility': visibility
        }
        if user_id:
            kb_create_dict['user_id'] = user_id

        try:
            await self.kb_service.create_knowledgebase(kb_create_dict)
        except exceptions.CannotCreateKnowledgeBase as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create knowledgebase: {str(e)}")
        except exceptions.KBException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"An unknown error occurred: failed to create knowledgebase: {str(e)}")

        try:
            upload_summary = await self.kb_service.add_files_to_filestore(user_id, remote_dir, knowledgebase_id, name, files, visibility)
            return upload_summary
        except exceptions.KBException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File handling error: {str(e)}")

    async def add_resources(self, kb_id: str, files: List[UploadFile], user_id: Optional[str]) -> UploadSummary:
        """
        Add one or more resources to a specific knowledge base.
        Handles file uploads and resource creation.
        """
        kb = await self.get_knowledgebase(kb_id)
        self.check_permission(kb, user_id)

        remote_dir = kb.remote_dir

        try:
            upload_summary = await self.kb_service.add_files_to_filestore(user_id, remote_dir, kb_id, kb.name, files, kb.visibility)
            return upload_summary
        except exceptions.KBException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File handling error: {str(e)}")

    async def rename_knowledgebase(self, kb_id: str, new_name: str, user_id: Optional[str]) -> None:
        """
        Update the name of a specific knowledge base.
        """
        kb = await self.get_knowledgebase(kb_id)
        self.check_permission(kb, user_id)

        try:
            await self.kb_service.update_knowledgebase(kb_id, {'name': new_name})
        except exceptions.InvalidNameError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name.")
        except exceptions.KBException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unknown error occurred when updating knowledge base for ID {kb_id}: {str(e)}")

    async def rename_resource(self, resource_id: str, new_name: str, user_id: Optional[str]) -> None:
        """
        Update the name of a specific resource.
        """
        resource = await self.get_resource(resource_id)
        self.check_permission(resource, user_id)

        try:
            await self.kb_service.update_resource(resource_id, {'name': new_name})
        except exceptions.InvalidNameError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name.")
        except exceptions.ResourceException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unknown error occurred when attempting to update resource name for ID {resource_id}: {str(e)}")

    async def move_resource_to_another_kb(self, source_kb_id: str, target_kb_id: str, resource_id: str, user_id: Optional[str]) -> None:
        """
        Move a resource from one knowledge base to another.
        """
        source_kb = await self.get_knowledgebase(source_kb_id)
        target_kb = await self.get_knowledgebase(target_kb_id)
        self.check_permission(source_kb, user_id)
        self.check_permission(target_kb, user_id)

        resource = await self.get_resource(resource_id)
        self.check_permission(resource, user_id)

        try:
            await self.kb_service.move_file_in_file_store(resource, new_dir=target_kb.remote_dir)
        except exceptions.RemoteFileManagerMoveError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error moving file in file store: {str(e)}")

        try:
            await self.remove_resources_from_kb(source_kb_id, [resource_id], user_id)
            await self.kb_service.add_resources(kb_id=target_kb_id, resources=[resource])
        except exceptions.KBException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unknown error occurred when moving resource to another knowledge base: {str(e)}")

    async def delete_resources(self, resource_ids: List[str], user_id: Optional[str]) -> None:
        """
        Delete resource by their ID.
        """
        for resource_id in resource_ids:
            resource = await self.get_resource(resource_id)
            self.check_permission(resource, user_id)

        try:
            await self.kb_service.delete_file_from_file_store(resource.remote_file_key)
        except exceptions.RemoteFileManagerDeleteError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting file from file store: {str(e)}")

        try:
            await self.kb_service.delete_resources(resource_ids)
        except exceptions.CannotDeleteResource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"One or more resources not found for deletion")
        except exceptions.ResourceException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unknown error occurred when attempting to delete resources: {str(e)}")

    async def delete_knowledgebase(self, kb_id: str, user_id: Optional[str]) -> None:
        """
        Delete a knowledge base by its ID and all its associated resources.
        """
        kb = await self.get_knowledgebase(kb_id)
        self.check_permission(kb, user_id)

        try:
            await self.kb_service.delete_directory_from_file_store(kb.remote_dir)
        except exceptions.RemoteFileManagerDeleteError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting knowledgebase: {str(e)}")

        try:
            await self.kb_service.delete_knowledgebase(kb_id)
        except exceptions.KBException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unknown error occurred when attempting to delete knowledge base with ID {kb_id}: {str(e)}")
