from typing import Dict, Union
from pydantic import BaseModel


# ------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------- #
#  Base Error Models

class ErrorModel(BaseModel):
    detail: Union[str, Dict[str, str]]

# Pydantic model for error codes and reasons


class ErrorCodeReasonModel(BaseModel):
    code: str
    reason: str


class InvalidNameError(Exception):
    pass


class PermissionDenied(Exception):
    pass


# ------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------- #
#  Knowledgebase Exceptions

# Base exception for all chat-related errors
class KBException(Exception):
    pass


class KnowledgeBaseNotFound(KBException):
    pass


class KnowledgeBasesForUserNotFound(KBException):
    pass


class InvalidPathError(KBException):
    pass


class CannotCreateKnowledgeBase(KBException):
    pass


class CannotUpdateKnowledgeBase(KBException):
    pass


class CannotUploadFile(KBException):
    pass


class ResourcesForKnowledgeBaseNotFound(KBException):
    pass


class ResourceAdditionError(KBException):
    """Exception raised when adding a resource to a knowledge base fails."""
    pass


class CannotDeleteKnowledgeBase(KBException):
    """Exception raised when a knowledge base cannot be deleted."""
    pass


class CannotDeleteResource(KBException):
    """Exception raised when a resource cannot be deleted."""
    pass


class KnowledgeBaseDeleteError(CannotDeleteKnowledgeBase):
    """Exception raised when deletion of a knowledge base fails."""
    pass


class ResourceDeleteError(CannotDeleteResource):
    """Exception raised when deletion of a resource fails."""
    pass


# ------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------- #
#  Resource Exceptions

class ResourceException(Exception):
    """Base exception for all resource-related errors."""
    pass


class ResourceNotFound(ResourceException):
    """Exception raised when a resource cannot be found."""
    pass


class CannotCreateResource(ResourceException):
    """Exception raised when a resource cannot be created."""

    def __init__(self, message: str = "Failed to create resource."):
        super().__init__(message)


class CannotUpdateResource(ResourceException):
    """Exception raised when a resource cannot be updated."""
    pass


class CannotDeleteResource(ResourceException):
    """Exception raised when a resource cannot be deleted."""
    pass


# ------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------- #
#  Remote File Manager Exceptions


class RemoteFileManagerException(Exception):
    pass


class RemoteFileManagerAddError(RemoteFileManagerException):
    pass


class RemoteFileManagerMoveError(RemoteFileManagerException):
    pass


class RemoteFileManagerDeleteError(RemoteFileManagerException):
    pass
