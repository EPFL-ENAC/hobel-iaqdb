import os
from motor.motor_asyncio import AsyncIOMotorClient

# Load the MongoDB connection string from the environment variable MONGODB_URI
MONGODB_URI = os.environ['MONGODB_URI']

client = {}


def init_client():
    client = AsyncIOMotorClient(MONGODB_URI)
    return client
