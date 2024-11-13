from typing import List, Dict, Union, Any, Optional, Tuple
import re

# FastAPI
from fastapi import UploadFile

# Import The Adapters and Other Services
from app.adapters import KnowledgeBaseAdapter, ResourceAdapter
from app.services import RemoteFileService

# Import the resource document
from app.models import ResourceDocument, KnowledgeBaseDocument, Visibility

# Schemas
from app.schemas import FileUploadError, FileUploadSuccess, UploadSummary

# Exceptions
from app import exceptions


class KnowledgeBaseService:
    """
    Business logic layer that handles operations on knowledge bases and their resources.
    """

    def __init__(self, kb_adapter: KnowledgeBaseAdapter, resource_adapter: ResourceAdapter, remote_file_service: RemoteFileService):
        """
        Initialize with knowledge base database, resource adapter, and remote file service.
        """
        self.kb_adapter = kb_adapter
        self.resource_adapter = resource_adapter
        self.remote_file_service = remote_file_service

    # Helper Methods
    # ------------------------------------------------------------------------------------------------------------------------- #

    async def _update_resource_metadata_in_kb(self, kb_id: str, resource_id: str, updates: Dict[str, Any]) -> None:
        """
        Update the metadata of a resource within a knowledge base.
        """
        try:
            kb_doc = await self.get_knowledgebase_by_id(kb_id)
            updated = False
            for resource in kb_doc.resources:
                if resource.resource_id == resource_id:
                    for key, value in updates.items():
                        if hasattr(resource, key):
                            setattr(resource, key, value)
                    updated = True
                    break
            if updated:
                await self.kb_adapter.update_kb(kb_id, {'resources': kb_doc.resources})
        except Exception as e:
            raise exceptions.KBException(f"An unknown error occurred when updating resource metadata in knowledge base for ID {kb_id}: {str(e)}")

    # Get Methods
    # ------------------------------------------------------------------------------------------------------------------------- #
    # ------------------------------------------------------------------------------------------------------------------------- #

    async def get_knowledgebase_by_id(self, kb_id: str) -> KnowledgeBaseDocument:
        """
        Retrieve a single knowledge base by its ID.
        """
        try:
            return await self.kb_adapter.get_kb_by_id(kb_id)
        except exceptions.KnowledgeBaseNotFound as e:
            raise e
        except Exception as e:
            raise exceptions.KBException(f"An unknown error occurred when retrieving knowledge base {kb_id}: {str(e)}")

    async def get_resource_by_id(self, resource_id: str) -> ResourceDocument:
        """
        Retrieve a single resource by its ID.
        """
        try:
            return await self.resource_adapter.get(resource_id)
        except exceptions.ResourceNotFound as e:
            raise e
        except Exception as e:
            raise exceptions.ResourceException(f"An unknown error occurred when attempting to retrieve resource with ID {resource_id}: {str(e)}")

    async def get_all_resources_by_user_id(self, user_id: str) -> List[ResourceDocument]:
        """
        Retrieve all resources associated with a specific user ID.
        """
        try:
            return await self.resource_adapter.get_all_by_user_id(user_id)
        except exceptions.ResourceNotFound as e:
            raise e
        except Exception as e:
            raise exceptions.ResourceException(f"An unknown error occurred when attempting to retrieve resources for user ID {user_id}: {str(e)}")

    async def get_all_knowledgebases_by_user_id(self, user_id: str) -> List[KnowledgeBaseDocument]:
        """
        Retrieve all knowledge bases associated with a specific user ID.
        """
        try:
            return await self.kb_adapter.get_all_by_user_id(user_id)
        except exceptions.KnowledgeBasesForUserNotFound as e:
            raise e
        except Exception as e:
            raise exceptions.KBException(f"An unknown error occurred when retrieving knowledge bases for user {user_id}: {str(e)}")

    # Create Methods
    # ------------------------------------------------------------------------------------------------------------------------- #
    # ------------------------------------------------------------------------------------------------------------------------- #

    async def create_knowledgebase(self, create_dict: Dict[str, Any]) -> KnowledgeBaseDocument:
        """
        Create a new knowledge base document from the provided dictionary.
        """
        try:
            return await self.kb_adapter.create(create_dict)
        except exceptions.CannotCreateKnowledgeBase as e:
            raise e
        except Exception as e:
            raise exceptions.KBException(f"An unknown error occurred during knowledge base creation: {str(e)}")

    async def create_resource(self, create_dict: Dict[str, Any]) -> ResourceDocument:
        """
        Create a new resource document from the provided dictionary.
        """
        try:
            return await self.resource_adapter.create_resource(create_dict)
        except exceptions.CannotCreateResource as e:
            raise e
        except Exception as e:
            raise exceptions.ResourceException(f"An unknown error occurred when attempting to create a resource: {str(e)}")

    # Update Methods
    # ------------------------------------------------------------------------------------------------------------------------- #
    # ------------------------------------------------------------------------------------------------------------------------- #

    async def add_resources(self, kb_id: str, resources: Union[ResourceDocument, List[ResourceDocument]]) -> None:
        """
        Add one or more resources to a specific knowledge base.
        Handles both single and multiple resources.
        """
        try:
            await self.kb_adapter.add_resources(kb_id, resources)
        except exceptions.ResourceAdditionError as e:
            raise e
        except Exception as e:
            raise exceptions.KBException(f"An unknown error occurred when trying to add resources to knowledge base with ID {kb_id}: {str(e)}")

    async def update_knowledgebase(self, kb_id: str, updates: Dict[str, Any]) -> None:
        """
        Update specific fields of a knowledge base.
        """
        try:
            await self.kb_adapter.update_kb(kb_id, updates)
        except exceptions.InvalidNameError as e:
            raise e
        except Exception as e:
            raise exceptions.KBException(f"An unknown error occurred when updating knowledge base for ID {kb_id}: {str(e)}")

    async def update_resource(self, resource_id: str, updates: Dict[str, Any]) -> None:
        """
        Update specific fields of a resource.
        """
        try:
            await self.resource_adapter.update_resource(resource_id, updates)

            resource_doc = await self.get_resource_by_id(resource_id)
            knowledgebase_id = resource_doc.knowledgebase_id

            if knowledgebase_id:
                await self._update_resource_metadata_in_kb(knowledgebase_id, resource_id, updates)
        except exceptions.InvalidNameError as e:
            raise e
        except Exception as e:
            raise exceptions.ResourceException(f"An unknown error occurred when attempting to update resource for ID {resource_id}: {str(e)}")

    # Remove Methods
    # ------------------------------------------------------------------------------------------------------------------------- #
    # ------------------------------------------------------------------------------------------------------------------------- #

    async def remove_resources_from_kb(self, kb_id: str, resource_ids: Union[str, List[str]]) -> None:
        """
        Remove one or more resource's metadata by their IDs from a specific knowledge base.
        """
        if not isinstance(resource_ids, list):
            resource_ids = [resource_ids]

        try:
            await self.kb_adapter.remove_resources(kb_id, resource_ids)
        except exceptions.KnowledgeBaseNotFound as e:
            raise e
        except exceptions.ResourceDeleteError as e:
            raise e
        except Exception as e:
            raise exceptions.KBException(f"An unknown error occurred when attempting to remove resources from knowledge base with ID {kb_id}: {str(e)}")

    # Delete Methods
    # ------------------------------------------------------------------------------------------------------------------------- #
    # ------------------------------------------------------------------------------------------------------------------------- #

    async def delete_resources(self, resource_ids: List[str]) -> None:
        """
        Delete resources by their IDs.
        """
        for resource_id in resource_ids:
            try:
                await self.resource_adapter.delete_resource(resource_id)
            except exceptions.CannotDeleteResource as e:
                raise e  # Re-raising as it's crucial for transactional integrity.
            except Exception as e:
                raise exceptions.ResourceException(f"An unknown error occurred when attempting to delete resource with ID {resource_id}: {str(e)}")

    async def delete_knowledgebase(self, kb_id: str) -> None:
        """
        Delete a knowledge base by its ID and all its associated resources.
        """
        try:
            await self.kb_adapter.delete(kb_id)
        except Exception as e:
            raise exceptions.KBException(f"An unknown error occurred when attempting to delete knowledge base with ID {kb_id}: {str(e)}")

    # File Handling Methods
    # ------------------------------------------------------------------------------------------------------------------------- #
    # ------------------------------------------------------------------------------------------------------------------------- #

    async def add_file_to_filestore(self,
                                    file: UploadFile,
                                    remote_dir: str,
                                    knowledgebase_id: str,
                                    knowledgebase_name: str,
                                    visibility: Visibility,
                                    user_id: Optional[str] = None
                                    ) -> Tuple[bool, Union[ResourceDocument, str]]:
        """
        Manages the upload and resource creation for a single file.
        """
        resource_dict = {
            'name': file.filename,
            'knowledgebase_id': knowledgebase_id,
            'knowledgebase_name': knowledgebase_name,
        }

        if user_id:
            resource_dict['user_id'] = user_id

        try:
            resource = await self.create_resource(resource_dict)
            resource_id = resource.id
        except Exception as ex:
            return False, str(ex)

        tags = {
            'visibility': visibility,
            'resource_id': resource_id,
            'knowledgebase_id': knowledgebase_id
        }
        if user_id:
            tags['user_id'] = user_id

        upload_response = await self.remote_file_service.upload_file(file=file, dir_path=remote_dir, file_name=file.filename, tags=tags)
        if not upload_response.success:
            return False, upload_response.message

        try:
            await self.update_resource(resource_id, {'remote_file_key': upload_response.file_key})
            return True, resource
        except Exception as ex:
            await self.remote_file_service.delete_file(upload_response.file_key)
            return False, str(ex)

    async def add_files_to_filestore(self,
                                     user_id: Optional[str],
                                     remote_dir: str,
                                     knowledgebase_id: str,
                                     knowledgebase_name: str,
                                     files: List[UploadFile],
                                     visibility: Visibility) -> UploadSummary:
        """
        Handles file uploads and resource creation for a knowledgebase.
        """
        successes: List[FileUploadSuccess] = []
        errors: List[FileUploadError] = []

        for file in files:
            success, result = await self.handle_single_file(file, remote_dir, knowledgebase_id, knowledgebase_name, visibility, user_id)
            if success:
                successes.append(FileUploadSuccess(filename=file.filename, resource=result))
            else:
                errors.append(FileUploadError(filename=file.filename, error_message=str(result)))

            await file.close()

        if successes:
            try:
                await self.add_resources(knowledgebase_id, [success.resource for success in successes])
            except (exceptions.ResourceAdditionError, exceptions.KBException) as e:
                raise exceptions.RemoteFileManagerAddError(f"Files parsed successfully buy failed to add resources to knowledge base: {str(e)}")

        return UploadSummary(successes=successes, errors=errors)


    async def move_file_in_file_store(self, resource: ResourceDocument, new_dir: str) -> None:
        """
        Handles file movements between directories.
        """
        try:
            old_key = resource.remote_file_key
            response = await self.remote_file_service.move_file(old_key, new_dir, resource.name)
            if response.success:
                resource.remote_file_key = response.file_key
                await resource.save()
            else:
                raise exceptions.RemoteFileManagerMoveError(f"An error occurred while moving the file: {response.message}")
        except exceptions.RemoteFileManagerMoveError:
            raise
        except Exception as e:
            raise exceptions.RemoteFileManagerMoveError(f"An unknown error occurred while moving the file: {str(e)}")

    async def delete_file_from_file_store(self, file_key: str) -> None:
        """
        Handles the deletion of files from the file store.
        """
        try:
            response = await self.remote_file_service.delete_file(file_key)
            if not response.success:
                raise exceptions.RemoteFileManagerDeleteError(f"An error occurred while deleting the file: {response.message}")
        except exceptions.RemoteFileManagerDeleteError:
            raise
        except Exception as e:
            raise exceptions.RemoteFileManagerDeleteError(f"An unknown error occurred while deleting the file: {str(e)}")

    async def delete_directory_from_file_store(self, dir_key: str) -> None:
        """
        Handles the deletion of directories from the file store.
        """
        try:
            response = await self.remote_file_service.delete_directory(dir_key)
            if not response.success:
                raise exceptions.RemoteFileManagerDeleteError(f"An error occurred while deleting the directory: {response.message}")
        except exceptions.RemoteFileManagerDeleteError:
            raise
        except Exception as e:
            raise exceptions.RemoteFileManagerDeleteError(f"An unknown error occurred while deleting the directory: {str(e)}")