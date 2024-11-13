# Typing
from typing import Optional

# Motor Asyncio
import motor.motor_asyncio

# Import configuration
from app.config import workmait_config


class MongoClient:
    """Singleton pattern for a mongodb connection"""
    _instance: Optional['MongoClient'] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, uuid_representation: str = "standard"):

        # check UUID representation
        if uuid_representation != "standard":
            raise ValueError("UUID Representation needs to be 'standard'.")

        # Mongo connection string
        self.mongo_connection_str = workmait_config.MONGO_CONNECTION_STR

        # Initialize the MongoDB client
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_connection_str, uuidRepresentation=uuid_representation)

    @staticmethod
    def get_connection():
        if MongoClient._instance is None:
            MongoClient()
        return MongoClient._instance.client