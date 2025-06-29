from typing import Optional
from pymongo import ASCENDING, DESCENDING, AsyncMongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "fastapi_tasks")

# Global variables for MongoDB client and database
mongo_client: Optional[AsyncMongoClient] = None
db = None
tasks_collection = None


async def connect_to_mongo():
    """Create database connection"""
    global mongo_client, db, tasks_collection

    try:
        print(f"Connecting to MongoDB at {MONGODB_URL}")

        # Create client with timeout settings
        mongo_client = AsyncMongoClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,  # 5 seconds timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=10,
            retryWrites=True
        )

        # Test the connection
        await mongo_client.admin.command('ping')
        print("Successfully connected to MongoDB")

        # Initialize database and collection
        db = mongo_client[MONGODB_DB]
        tasks_collection = db["tasks"]

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"Failed to connect to MongoDB: {e}")
        print("Make sure MongoDB is running and accessible")
        raise e
    except Exception as e:
        print(f"Unexpected error connecting to MongoDB: {e}")
        raise e


async def disconnect_from_mongo():
    """Close database connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("Disconnected from MongoDB")


# Ensure indexes
async def ensure_indexes():
    """Ensure MongoDB indexes"""
    if tasks_collection == None:
        print("Tasks collection not initialized, skipping index creation")
        return

    try:
        print("Ensuring MongoDB indexes...")
        await tasks_collection.create_index([("user_id", ASCENDING)])
        await tasks_collection.create_index([("created_at", DESCENDING)])
        await tasks_collection.create_index([("updated_at", DESCENDING)])
        await tasks_collection.create_index([("deleted_at", DESCENDING)])
        await tasks_collection.create_index([("completed_at", DESCENDING)])
        print("MongoDB indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {e}")
        # Don't raise the error as this shouldn't stop the application
