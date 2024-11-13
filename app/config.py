# Load Environment variables
import os
from dotenv import load_dotenv

# Pydantic
from pydantic import BaseModel

# Load the environment variables
load_dotenv()


class WorkmaitConfig(BaseModel):

    # MongoDB
    MONGO_CONNECTION_STR: str = os.getenv('MONGO_CONNECTION_STR')

    # SECRET
    SECRET: str = ""

    # OpenAI API KEY
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')

    # Boto3
    AWS_ACCESS_KEY_ID: str = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY: str = os.getenv('AWS_SECRET_ACCESS_KEY')


# Instance of config
workmait_config = WorkmaitConfig()
