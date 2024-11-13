from typing import List, Optional, Type, Dict, Any, Union

# Beanie Imports
from beanie import Document, PydanticObjectId, DeleteRules

# Model Imports
from app.models import KnowledgeBaseDocument, ResourceMetadata, ResourceDocument

# Import Exceptions
from app import exceptions


class KnowledgeBaseAdapter:
    """
    Simplified database adapter for Beanie to manage knowledge base documents.
    """

    def __init__(self,
                 kb_model: Type[KnowledgeBaseDocument],
                 resource_model: Type[ResourceDocument]):
        """
        Initialize with knowledge base model and a resource manager.
        """
        self.kb_model = kb_model
        self.resource_model = resource_model

    # ------------------------------------------------------------------------------------------------------------------------- #
    # Get Methods

    async def get_kb_by_id(self, kb_id: str) -> Optional[KnowledgeBaseDocument]:
        """
        Retrieve a single knowledge base by its ID.
        """
        if not kb_id:
            raise exceptions.InvalidPathError("The provided KB ID is invalid.")

        kb = await self.kb_model.find_one(self.kb_model.id == kb_id)
        if not kb:
            raise exceptions.KnowledgeBaseNotFound("Knowledge Base not found.")

        return kb

    async def get_all_by_user_id(self, user_id: str) -> List[KnowledgeBaseDocument]:
        """
        Retrieve all knowledge bases associated with a specific user ID.
        """
        all_knowledgebases = await self.kb_model.find(self.kb_model.user_id == PydanticObjectId(user_id)).to_list()
        if not all_knowledgebases:
            raise exceptions.KnowledgeBasesForUserNotFound("No Knowledge Bases found for the given user.")

        return all_knowledgebases

    async def get_all_resources(self, kb_id: str) -> List[ResourceMetadata]:
        """
        Retrieve all resources associated with a knowledge base ID, returning a list of resource metadata.
        If no resources are found, raises ResourcesForKnowledgeBaseNotFound.
        """
        kb = await self.get_kb_by_id(kb_id)
        if not kb.resources:
            raise exceptions.ResourcesForKnowledgeBaseNotFound("No resources found for the specified knowledge base.")

        return kb.resources

    # ------------------------------------------------------------------------------------------------------------------------- #
    # Create Method

    async def create(self, create_dict: Dict[str, Any]) -> KnowledgeBaseDocument:
        """
        Create a new knowledge base document from the provided dictionary.
        """
        try:
            kb = self.kb_model(**create_dict)
            await kb.create()
            return kb
        except Exception as e:
            raise exceptions.CannotCreateKnowledgeBase(f"Failed to create Knowledge Base: {str(e)}")

    # ------------------------------------------------------------------------------------------------------------------------- #
    # Update Method

    async def update_kb(self, kb_id: str, update_dict: Dict[str, Any]) -> None:
        """
        Update specific fields of a kb based on a provided dictionary.
        """
        kb = await self.get_kb_by_id(kb_id)

        # Perform any necessary validation before updating fields
        if 'name' in update_dict:
            new_name = update_dict['name'].strip()
            if new_name == "":
                raise exceptions.InvalidNameError("The new name provided is invalid.")
            kb.name = new_name

        # Update other fields if necessary
        for key, value in update_dict.items():
            if key != 'name':  # 'name' is already handled
                setattr(kb, key, value)

        try:
            await kb.save()
        except Exception as e:
            raise exceptions.CannotUpdateKnowledgeBase(f"Failed to update resource for ID {kb_id}: {str(e)}")

    async def add_resources(self, kb_id: str, resources: Union[ResourceDocument, List[ResourceDocument]]) -> None:
        """
        Add one or more resources to a specific knowledge base.
        This method handles both single and multiple resources.
        """
        # Ensure resources is a list even if a single ResourceDocument is provided
        if not isinstance(resources, list):
            resources = [resources]

        try:
            kb = await self.get_kb_by_id(kb_id)

            # Convert each resource document to metadata
            resource_metadata_list = [res.to_metadata() for res in resources]

            # Initialize resources if it doesn't exist
            if not hasattr(kb, 'resources') or kb.resources is None:
                kb.resources = []

            # Append new resource metadata to the existing list
            kb.resources.extend(resource_metadata_list)

            # Save the knowledge base with the updated resources list
            await kb.save()
        except Exception as e:  # Consider catching a more specific exception if possible
            raise exceptions.ResourceAdditionError(f"Failed to add resources to knowledge base with ID {kb_id}: {str(e)}")

    async def remove_resources(self, kb_id: str, resource_ids: Union[str, List[str]]) -> None:
        """
        Remove one or more resource's metadata by their IDs from a specific knowledge base.
        """
        if not isinstance(resource_ids, list):
            resource_ids = [resource_ids]

        try:
            kb = await self.get_kb_by_id(kb_id)
            original_length = len(kb.resources)

            kb.resources = [res for res in kb.resources if res.resource_id not in resource_ids]

            if len(kb.resources) == original_length:
                raise exceptions.ResourceDeleteError("No resources with the specified IDs were found in the knowledge base with ID {kb_id}.")

            await kb.save()
        except Exception as e:
            raise exceptions.KBException(f"Failed to remove resources from knowledge base with ID {kb_id}: {str(e)}")

    # ------------------------------------------------------------------------------------------------------------------------- #
    # Delete Methods

    async def delete(self, kb_id: str) -> None:
        """
        Delete a knowledge base by its ID and all its associated resources. Uses Beanie's DELETE_LINKS rule to ensure all linked resources are also deleted.
        """
        try:
            kb = await self.get_kb_by_id(kb_id)
            await kb.delete(link_rule=DeleteRules.DELETE_LINKS)
        except Exception as e:
            raise exceptions.KnowledgeBaseDeleteError(f"Failed to delete knowledge base with ID {kb_id}: {str(e)}")
