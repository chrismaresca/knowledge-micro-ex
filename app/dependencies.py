# FastAPI Depends
from fastapi import Depends

# Import the Clients
from app.clients import RedisClient, RemoteFileServiceClient, S3Client, MongoClient

# Import s3 Manager
from app.services import (KnowledgeBaseService,
                          RemoteFileService,
                          S3Service,
                          AppService)


# Import Models and Adapters
from app.models import ResourceDocument
from app.adapters import ResourceAdapter, KnowledgeBaseAdapter



def get_redis_client():
    """
    Get the redis client.
    """
    return RedisClient()


# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# Remote File Service Dependencies


def get_remote_file_service_client() -> RemoteFileServiceClient:
    """
    Get the remote file service client.
    """
    return S3Client.get_resource()


def get_remote_file_service(client: RemoteFileServiceClient = Depends(get_remote_file_service_client)) -> RemoteFileService:
    """
    Get the Remote File service. This depends on the client.
    """
    return S3Service(s3_client_connection=client, bucket_name="workmaitblogimages")


# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------------------------------------------- #
# Dependency Callable for Knowledge Service


async def get_kb_adapter():
    yield KnowledgeBaseAdapter(ResourceDocument)


async def get_resource_adapter():
    yield ResourceAdapter(ResourceDocument)


async def get_kb_service(kb_adpater=Depends(get_kb_adapter), resource_adapter=Depends(get_resource_adapter)):
    yield KnowledgeBaseService(kb_adapter=kb_adpater, resource_adapter=resource_adapter)


async def get_app_service(knowledge_handler=Depends(get_kb_service), remote_file_service=Depends(get_remote_file_service)):
    """
    Yield the KB Application Service
    """
    yield AppService(knowledge_handler=knowledge_handler,
                     remote_file_service=remote_file_service)
