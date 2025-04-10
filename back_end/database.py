# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME

# Connect to MongoDB
client = AsyncIOMotorClient(MONGO_URI)
database = client[DB_NAME]
eid_collection = database["eids"]
