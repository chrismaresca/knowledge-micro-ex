from typing import List, Optional, Type, Dict, Any

# Beanie Imports
from beanie import PydanticObjectId

# Model Imports
from app.models import ResourceDocument

# Import Exceptions
from app import exceptions

# Import Exceptions
from app import exceptions


class ResourceAdapter:
    """
    Simplified database adapter for Beanie to manage resource documents.
    """

    def __init__(self, resource_model: Type[ResourceDocument]):
        """
        Initialize with resource model.
        """
        self.resource_model = resource_model

    # ------------------------------------------------------------------------------------------------------------------------- #
    # Get Methods

    async def get_resource_by_id(self, resource_id: str) -> Optional[ResourceDocument]:
        """
        Retrieve a single resource by its ID.
        """
        resource = await self.resource_model.find_one(self.resource_model.resource_id == resource_id)
        if not resource:
            raise exceptions.ResourceNotFound(f"Resource with ID {resource_id} not found.")
        return resource

    async def get_all_by_user_id(self, user_id: str) -> List[ResourceDocument]:
        """
        Retrieve all resources associated with a specific user ID.
        """
        resources = await self.resource_model.find(self.resource_model.user_id == user_id).to_list()
        if not resources:
            raise exceptions.ResourceNotFound(f"No resources found for user with ID {user_id}.")
        return resources

    async def get_most_recent(self, user_id: Optional[str] = None, knowledgebase_id: Optional[str] = None, limit: int = 5) -> List[ResourceDocument]:
        """
        Retrieve the most recent resources, optionally filtered by user or knowledge base, limited by a provided count.
        """
        query = {}
        if user_id:
            query["user_id"] = user_id
        if knowledgebase_id:
            query["knowledgebase_id"] = PydanticObjectId(knowledgebase_id)
        resources = await self.resource_model.find(query).sort("-date_last_modified").limit(limit).to_list()
        if not resources:
            raise exceptions.ResourceNotFound("No resources found matching the specified criteria.")
        return resources

    # ------------------------------------------------------------------------------------------------------------------------- #
    # Create Method

    async def create_resource(self, create_dict: Dict[str, Any]) -> ResourceDocument:
        """
        Create a new resource document from the provided dictionary.
        """
        try:
            resource = self.resource_model(**create_dict)
            await resource.create()
            return resource
        except Exception as e:
            raise exceptions.CannotCreateResource(f"Failed to create resource: {str(e)}")

    # ------------------------------------------------------------------------------------------------------------------------- #
    # Update Method

    async def update_resource(self, resource_id: str, update_dict: Dict[str, Any]) -> None:
        """
        Update specific fields of a resource based on a provided dictionary.
        """
        resource = await self.get_resource_by_id(resource_id)

        # Perform any necessary validation before updating fields
        if 'name' in update_dict:
            new_name = update_dict['name'].strip()
            if new_name == "":
                raise exceptions.InvalidNameError("The new name provided is invalid.")
            resource.name = new_name

        # Update other fields if necessary
        for key, value in update_dict.items():
            if key != 'name':  # 'name' is already handled
                setattr(resource, key, value)

        try:
            await resource.save()
        except Exception as e:
            raise exceptions.CannotUpdateResource(f"Failed to update resource for ID {resource_id}: {str(e)}")
    # ------------------------------------------------------------------------------------------------------------------------- #
    # Delete Methods

    async def delete_resource(self, resource_id: str) -> None:
        """
        Delete a resource by its ID.
        """
        resource = await self.get_resource_by_id(resource_id)
        try:
            await resource.delete()
        except Exception as e:
            raise exceptions.CannotDeleteResource(f"Failed to delete resource with ID {resource_id}: {str(e)}")
        

    async def delete_resource(self, resource_id: str) -> None:
        """
        Delete a resource by its ID.
        """
        resource = await self.get_resource_by_id(resource_id)
        try:
            await resource.delete()
        except Exception as e:
            raise exceptions.CannotDeleteResource(f"Failed to delete resource with ID {resource_id}: {str(e)}")


    # ------------------------------------------------------------------------------------------------------------------------- #
