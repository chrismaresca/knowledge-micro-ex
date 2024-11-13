# knowledgebase_router.py

from typing import Annotated, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel

# Import services
from app.services import AppService

# Import the Redis client
from app.clients import RedisClient

# Import Dependencies
from app.dependencies import get_app_service, get_redis_client
from app.firebase import get_current_user_no_role, get_current_user_with_role, BaseUser


# Import Schemas
from app.schemas import (

    # KB Requests
    CreateKnowledgebaseRequest,
    AddResourcesRequest,
    DeleteResourcesRequest,
    ShareKnowledgebaseRequest,
    RenameFileRequest,
    RenameKnowledgebaseRequest,

    # Redis Events
    ToLlamaDocsEventPayload
)


# Initialize a router
router = APIRouter()


def to_llama_docs_fn(to_llama_docs_payload: ToLlamaDocsEventPayload, redis_client: RedisClient):
    """
    Function to produce the TO_LLAMA_DOCS event.
    """
    redis_client.produce_event('TO_LLAMA_DOCS', to_llama_docs_payload)

# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# Create KB Route


# Create KB Route
@router.post("/create")
async def create_knowledgebase(
    app_service: Annotated[AppService, Depends(get_app_service)],
    redis_client: Annotated[RedisClient, Depends(get_redis_client)],
    background_tasks: BackgroundTasks,
    request_payload: CreateKnowledgebaseRequest,
    user: Annotated[Optional[BaseUser], Depends(get_current_user_no_role)]
):
    """
    Endpoint to create a knowledgebase.
    """
    user_id = user.id if user else None

    if not user_id and request_payload.visibility == 'private':
        raise HTTPException(status_code=400, detail="Cannot create a private kb for a non-authenticated user.")

    # Call the Function
    upload_summary = await app_service.create_knowledgebase(
        files=request_payload.files,
        name=request_payload.name,
        visibility=request_payload.visibility,
        user_id=user_id
    )

    # Get all of the file keys of the successful uploads
    remote_file_keys = [success.resource.remote_file_key for success in upload_summary.successes]
    to_llama_docs_payload = ToLlamaDocsEventPayload(remote_file_keys=remote_file_keys)

    # BackgroundTasks creates a separate thread --> Callable interface
    background_tasks.add_task(to_llama_docs_fn, to_llama_docs_payload, redis_client)

    return {"message": "Knowledgebase creation initiated", "upload_summary": upload_summary}

# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# Add Resources Routeƒ

# Add Resources Route


@router.post("/add-resources/{kb_id}")
async def add_resources(
    kb_id: str,
    app_service: Annotated[AppService, Depends(get_app_service)],
    redis_client: Annotated[RedisClient, Depends(get_redis_client)],
    background_tasks: BackgroundTasks,
    request_payload: AddResourcesRequest,
    user: Annotated[Optional[BaseUser], Depends(get_current_user_no_role)]
):
    upload_summary = await app_service.add_resources(
        kb_id=kb_id,
        files=request_payload.files,
        user_id=user.id if user else None
    )

    remote_file_keys = [success.resource.remote_file_key for success in upload_summary.successes]
    to_llama_docs_payload = ToLlamaDocsEventPayload(remote_file_keys=remote_file_keys)

    # BackgroundTasks creates a separate thread --> Callable interface
    background_tasks.add_task(to_llama_docs_fn, to_llama_docs_payload, redis_client)

    return {"message": "Resources added successfully", "upload_summary": upload_summary}
