# FastAPI
from fastapi import Depends, FastAPI, Request, HTTPException, Header
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

# Asyncronous context manager
from contextlib import asynccontextmanager

# initialize beanie when app starts
from beanie import init_beanie

# Imoort the Resource Doc and Knowledge Base Doc
from app.models import ResourceDocument, KnowledgeBaseDocument

# Import the S3 service
from app.services import S3Service

# Import the Mongo Client
from app.clients import MongoClient


# Routers Impport
from app.routers.knowledge import router as knowledgebase_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles resources before app startup (before requests come in) and after shutdown (once requests stop coming in)"""

    # Initialize the S3 Connection
    S3Service.initialize()

    # Get the Mongo Client
    mongo_client = MongoClient.get_connection()

    # Main Database for Workmait
    workmait_db = mongo_client['workmait_v3']

    # beanie initialization with the models that map to different collections in the db
    await init_beanie(database=workmait_db, document_models=[ResourceDocument, KnowledgeBaseDocument])

    yield

# Main Application
app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the knowledgebase router
app.include_router(knowledgebase_router, prefix="/knowledgebase", tags=["knowledgebase"])

